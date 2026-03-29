import uuid
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(JSON, default=dict)  # {"ro": "", "hu": "", "de": "", "en": ""}
    category = Column(String(50), nullable=False, default="other")
    unit = Column(String(50), default="buc")
    base_price = Column(Float, nullable=False, default=0.0)
    assembly_ids = Column(JSON, default=list)  # list of Assembly IDs
    part_ids = Column(JSON, default=list)  # list of Part IDs
    assembly_steps = Column(JSON, default=list)  # list of AssemblyStep dicts
    notes = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    stock_movements = relationship("StockMovement", back_populates="product")
    offer_items = relationship("OfferItem", back_populates="product")
