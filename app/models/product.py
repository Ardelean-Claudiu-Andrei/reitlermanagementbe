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
    description = Column(JSON, default=dict)         # {"ro": "", "hu": "", "de": "", "en": ""}
    category = Column(String(50), nullable=False, default="other")
    unit = Column(String(50), default="buc")
    base_price = Column(Float, nullable=False, default=0.0)
    assembly_ids = Column(JSON, default=list)        # list of Assembly IDs (legacy)
    part_ids = Column(JSON, default=list)            # list of Part IDs (legacy)
    product_assemblies = Column(JSON, default=list)  # [{assemblyId, quantity}] — new format
    product_parts = Column(JSON, default=list)       # [{partId, quantity}] — new format
    assembly_steps = Column(JSON, default=list)      # product-level production steps (existing field)
    production_steps = Column(JSON, default=list)    # alias kept separate for forward compat
    notes = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    requires_purchase = Column(Boolean, nullable=False, default=False)
    purchase_supplier = Column(String(300), default="")
    purchase_price = Column(Float, nullable=True)
    purchase_currency = Column(String(10), default="EUR")
    purchase_vat_included = Column(Boolean, nullable=False, default=False)
    purchase_vat_rate = Column(Float, nullable=False, default=21.0)
    purchase_agent_contact = Column(String(300), default="")
    purchase_details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    stock_movements = relationship("StockMovement", back_populates="product")
    offer_items = relationship("OfferItem", back_populates="product")
