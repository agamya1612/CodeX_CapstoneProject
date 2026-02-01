# CodeX

CodeX is a distributed online code execution platform that allows users to submit source code and receive execution results asynchronously.  
It is built using FastAPI, Kafka, and PostgreSQL with a scalable worker-based architecture.

---

## Features

- User authentication using JWT
- Asynchronous code execution with Kafka
- Scalable execution workers
- RESTful API built with FastAPI
- Dockerized development and deployment

---

## Tech Stack

### Backend
- Python 3.11
- FastAPI
- SQLAlchemy
- Pydantic v2
- PostgreSQL
- Apache Kafka
- Passlib (bcrypt)

### Infrastructure
- Docker
- Docker Compose

---

## Project Structure

app/
├── api/
│ └── routes/
├── Models/
├── Services/
│ ├── kafka_producer.py
│ └── kafka_consumer.py
├── workers/
│ └── worker_execution.py
├── config.py
├── database.py
└── main.py# CodeX_CapstoneProject
