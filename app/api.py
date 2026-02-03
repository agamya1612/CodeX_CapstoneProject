# app/api.py
from fastapi import FastAPI, HTTPException, Depends
from kafka import KafkaProducer, KafkaConsumer
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from pydantic import BaseModel
from typing import Optional
import json
import uuid
import time
import threading
import os

from app.db import engine, Base, SessionLocal
from app import models

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "coderank-kafka:9092")
SUBMISSION_TOPIC = "code.submissions"
RESULTS_TOPIC = "code.results"


# -------------------- #
# DB Dependency
# -------------------- #
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------- #
# Kafka Producer (lazy)
# -------------------- #
producer = None

def get_producer():
    global producer
    if producer is None:
        while True:
            try:
                producer = KafkaProducer(
                    bootstrap_servers=KAFKA_BOOTSTRAP,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                )
                print("✅ API Kafka producer connected")
                break
            except Exception as e:
                print("⏳ API waiting for Kafka producer...", e)
                time.sleep(3)
    return producer


# -------------------- #
# Kafka Consumer -> Update DB
# -------------------- #
def consume_results_forever():
    while True:
        try:
            consumer = KafkaConsumer(
                RESULTS_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                group_id="api-results-consumer",
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
            print("✅ API Kafka consumer connected (code.results)")

            for msg in consumer:
                result = msg.value
                submission_id = result.get("id")

                if not submission_id:
                    continue

                db = SessionLocal()
                try:
                    job = db.query(models.Job).filter(models.Job.id == submission_id).first()
                    if job:
                        job.status = "COMPLETED" if result.get("exit") == 0 else "FAILED"
                        job.output = result.get("stdout", "")
                        job.error = result.get("stderr", "")
                        db.commit()
                        print(f"✅ Updated DB for {submission_id} -> {job.status}")
                except Exception as e:
                    db.rollback()
                    print("❌ Failed updating DB from result:", e)
                finally:
                    db.close()

        except Exception as e:
            print("⏳ API retrying Kafka consumer...", e)
            time.sleep(5)


# -------------------- #
# Schemas
# -------------------- #
class Submission(BaseModel):
    language: str
    code: str
    input: Optional[str] = ""

class SubmissionResponse(BaseModel):
    submission_id: str
    status: str


# -------------------- #
# FastAPI app
# -------------------- #
app = FastAPI()

@app.on_event("startup")
def on_startup():
    # Wait for MySQL and create tables
    for _ in range(30):
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ DB connected and tables created")
            break
        except OperationalError as e:
            print("⏳ Waiting for MySQL...", e)
            time.sleep(2)
    else:
        raise RuntimeError("❌ MySQL not reachable after retries")

    # Start background Kafka consumer for results
    threading.Thread(target=consume_results_forever, daemon=True).start()


# -------------------- #
# Routes
# -------------------- #
@app.post("/submit", response_model=SubmissionResponse)
def submit(payload: Submission, db: Session = Depends(get_db)):
    submission_id = str(uuid.uuid4())

    job = models.Job(
        id=submission_id,
        language=payload.language,
        code=payload.code,
        input=payload.input,
        status="PENDING",
    )
    db.add(job)
    db.commit()

    message = {
        "id": submission_id,
        "language": payload.language,
        "code": payload.code,
        "input": payload.input,
    }

    prod = get_producer()
    prod.send(SUBMISSION_TOPIC, message)
    prod.flush()

    return {"submission_id": submission_id, "status": "PENDING"}


@app.get("/result/{submission_id}")
def get_result(submission_id: str, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == submission_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Submission not found")

    return {
        "submission_id": job.id,
        "status": job.status,
        "output": job.output,
        "error": job.error,
        "created_at": job.created_at,
    }
