import uuid
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    company_id = Column(String(36), ForeignKey("clients.id"), nullable=True)
    status = Column(String(20), nullable=False, default="draft")  # draft|pending|approved|rejected
    validity = Column(String(50), default="")  # ISO date string
    delivery_time_weeks = Column(Integer, default=4)
    items = Column(JSON, default=list)  # [{"productId": "", "unitPrice": 0, "quantity": 0, "notes": ""}]
    installation = Column(Float, default=0.0)
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Client", back_populates="quotes")
    projects = relationship("Project", back_populates="quote")
