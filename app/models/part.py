import uuid
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Part(Base):
    __tablename__ = "parts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(100), unique=True, index=True, nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(JSON, default=dict)                      # {"ro": "", "hu": "", "de": "", "en": ""}
    category = Column(String(100), default="")
    file_name = Column(String(255), default="")
    file_location = Column(String(500), default="")
    drawing_location = Column(String(500), default="")            # laser drawing location
    unit = Column(String(50), default="buc")
    base_price = Column(Float, nullable=False, default=0.0)
    minimum_stock = Column(Float, default=0.0)
    quantity = Column(Float, default=0.0)
    required_quantity = Column(Integer, default=1)
    location = Column(String(200), default="")                    # physical location
    physical_location = Column(String(300), default="")
    requires_laser_cutting = Column(Boolean, default=False)
    welding_drawing_location = Column(String(500), default="")
    bending_drawing_location = Column(String(500), default="")
    cad_location = Column(String(500), default="")
    technical_drawing_location = Column(String(500), default="")
    production_steps = Column(JSON, default=list)                 # [AssemblyStep dicts]
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
