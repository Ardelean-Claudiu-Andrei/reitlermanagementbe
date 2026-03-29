import uuid
from sqlalchemy import Column, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Part(Base):
    __tablename__ = "parts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    description = Column(JSON, default=dict)  # {"ro": "", "hu": "", "de": "", "en": ""}
    file_name = Column(String(255), default="")
    file_location = Column(String(500), default="")
    unit = Column(String(50), default="buc")
    base_price = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
