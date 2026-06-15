import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    entity_type = Column(String(20), nullable=False)   # 'assembly' | 'part' | 'product'
    entity_id = Column(String(36), nullable=False)
    file_category = Column(String(50), nullable=False)  # 'dxf' | 'pdf' | 'image' | 'welding_drawing' | 'bending_drawing'
    original_filename = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)   # relative to static/uploads/
    content_type = Column(String(100), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
