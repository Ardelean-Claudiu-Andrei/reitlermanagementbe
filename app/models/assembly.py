import uuid
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Assembly(Base):
    __tablename__ = "assemblies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(JSON, default=dict)         # {"ro": "", "hu": "", "de": "", "en": ""}
    parts = Column(JSON, default=list)               # [{"partId": "", "quantity": 0}]
    child_assemblies = Column(JSON, default=list)    # [{"assemblyId": "", "quantity": 1}]
    composition_type = Column(String(50), default="standalone")  # "from_parts" | "from_assemblies" | "standalone"
    physical_location = Column(String(300), default="")
    welding_drawing_location = Column(String(500), default="")
    technical_drawing_location = Column(String(500), default="")
    cad_location = Column(String(500), default="")
    production_steps = Column(JSON, default=list)    # [AssemblyStep dicts]
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
