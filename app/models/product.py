import uuid
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    sku = Column(String(100), unique=True, index=True)
    price = Column(Float, nullable=False, default=0.0)
    unit = Column(String(50), default="buc")
    stock_quantity = Column(Float, default=0.0)
    min_stock_alert = Column(Float, default=0.0)
    image_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    category = relationship("Category", back_populates="products")
    stock_movements = relationship("StockMovement", back_populates="product")
    offer_items = relationship("OfferItem", back_populates="product")