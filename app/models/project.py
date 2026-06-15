import uuid
from sqlalchemy import Column, String, Float, DateTime, Text, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    company_id = Column(String(36), ForeignKey("clients.id"), nullable=True)
    quote_id = Column(String(36), ForeignKey("quotes.id"), nullable=True)
    status = Column(String(20), nullable=False, default="draft")  # draft|in-progress|done|cancelled
    start_date = Column(String(50), default="")  # ISO date string
    deadline = Column(String(50), default="")  # ISO date string
    finish_date = Column(String(50), nullable=True)
    warranty_expiration = Column(String(50), nullable=True)
    installation_cost = Column(Float, default=0.0)  # from quote, if any
    paid_amount = Column(Float, default=0.0)
    items = Column(JSON, default=list)  # [{"productId","quantity","unitPrice","notes","fromInventory"}]
    checklist = Column(JSON, default=list)  # [{"id","title","done","note","doneAt"}]
    issues = Column(JSON, default=list)  # [{"id","description","solved","solvedAt","createdAt"}]
    activity = Column(JSON, default=list)  # [{"id","action","user","timestamp"}]
    steps_completed = Column(JSON, default=list)  # [stepId, ...] — per-project production step completion
    steps_total = Column(Integer, default=0)      # cached total step count for quick progress in list view
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Client", back_populates="projects")
    quote = relationship("Quote", back_populates="projects")
