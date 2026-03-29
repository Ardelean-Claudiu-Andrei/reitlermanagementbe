import uuid
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    type = Column(String(20), nullable=False)  # "product" or "part"
    item_id = Column(String(36), nullable=False)  # references Product.id or Part.id
    quantity = Column(Float, default=0.0)
    min_stock = Column(Float, default=0.0)
    location = Column(String(200), default="")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
