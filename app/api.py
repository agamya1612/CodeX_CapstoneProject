from fastapi import FastAPI, HTTPException
from kafka import KafkaProducer, KafkaConsumer
import json
import uuid
import threading
import time
from pydantic import BaseModel

class Submission(BaseModel):
    language: str
    code: str
    input: str | None = ""


app = FastAPI()

producer = None
results = {}

def get_producer():
    global producer
    while producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers="kafka:9092",
                value_serializer=lambda v: json.dumps(v).encode()
            )
        except Exception:
            print("API waiting for Kafka...")
            time.sleep(5)
    return producer

def consume_results():
    while True:
        try:
            consumer = KafkaConsumer(
                "code.results",
                bootstrap_servers="kafka:9092",
                value_deserializer=lambda v: json.loads(v.decode()),
                group_id="api-results"
            )
            for msg in consumer:
                results[msg.value["id"]] = msg.value
        except Exception:
            print("API retrying result consumer...")
            time.sleep(5)

@app.on_event("startup")
def startup():
    threading.Thread(target=consume_results, daemon=True).start()

@app.post("/submit")
def submit(payload: Submission):
    submission_id = str(uuid.uuid4())
    data = payload.dict()
    data["id"] = submission_id

    get_producer().send("code.submissions", data)
    get_producer().flush()

    return {"submission_id": submission_id}

    

@app.get("/result/{submission_id}")
def get_result(submission_id: str):
    return results.get(submission_id, {"status": "RUNNING"})
