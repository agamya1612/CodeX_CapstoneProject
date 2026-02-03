from sqlalchemy import Column, String, Text, DateTime
from datetime import datetime
from app.db import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, index=True)
    language = Column(String(50), nullable=False)
    code = Column(Text, nullable=False)
    input = Column(Text)
    output = Column(Text)
    error = Column(Text)
    status = Column(String(20), default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
