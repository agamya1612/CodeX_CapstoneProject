from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class JobCreate(BaseModel):
    language: str
    code: str

class JobResponse(BaseModel):
    id: int
    language: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True  # IMPORTANT for SQLAlchemy
