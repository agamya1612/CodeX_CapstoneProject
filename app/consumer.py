import os
from kafka import KafkaConsumer, KafkaProducer
from app.executor import execute_code
import json
import time

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "coderank-kafka:9092")

def get_consumer():
    while True:
        try:
            return KafkaConsumer(
                "code.submissions",
                bootstrap_servers= BOOTSTRAP,
                value_deserializer=lambda v: json.loads(v.decode()),
                group_id="workers",
                auto_offset_reset="earliest"
            )
        except Exception as e:
            print("Worker waiting for Kafka...")
            time.sleep(5)

def get_producer():
    while True:
        try:
            return KafkaProducer(
                bootstrap_servers= BOOTSTRAP,
                value_serializer=lambda v: json.dumps(v).encode()
            )
        except Exception:
            print("Worker producer waiting for Kafka...")
            time.sleep(5)

consumer = get_consumer()
producer = get_producer()

print("Worker connected to Kafka")

for msg in consumer:
    job = msg.value
    print("Received job:", job)

    try:
        result = execute_code(
            job["language"],
            job["code"],
            job.get("input", "")
        )
    except Exception as e:
        result = {
            "stdout": "",
            "stderr": str(e),
            "exit": -1
        }

    result["id"] = job["id"]
    print("Sending result:", result)

    producer.send("code.results", result)
    producer.flush()
