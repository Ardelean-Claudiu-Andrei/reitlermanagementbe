import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Client(Base):
    __tablename__ = "clients"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    contact_person = Column(String(150), default="")
    email = Column(String(150), default="")
    phone = Column(String(50), default="")
    address = Column(String(500), default="")
    cui = Column(String(50), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    offers = relationship("Offer", back_populates="client")
    quotes = relationship("Quote", back_populates="company")
    projects = relationship("Project", back_populates="company")
