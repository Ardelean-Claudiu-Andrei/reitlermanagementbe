import enum
import uuid
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Text, Enum, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class OfferStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

class Offer(Base):
    __tablename__ = "offers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(Enum(OfferStatus), default=OfferStatus.DRAFT)
    valid_until = Column(Date)
    notes = Column(Text)
    total_amount = Column(Float, default=0.0)
    pdf_path = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    client = relationship("Client", back_populates="offers")
    creator = relationship("User")
    items = relationship("OfferItem", back_populates="offer", cascade="all, delete-orphan")

class OfferItem(Base):
    __tablename__ = "offer_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    offer_id = Column(String(36), ForeignKey("offers.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount_percent = Column(Float, default=0.0)
    line_total = Column(Float, nullable=False)

    offer = relationship("Offer", back_populates="items")
    product = relationship("Product", back_populates="offer_items")