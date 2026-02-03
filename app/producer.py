from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers="kafka:9092",
    value_serializer=lambda v: json.dumps(v).encode()
)

def submit_code(payload):
    producer.send("code.submissions", payload)
    producer.flush()