from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.mysql import LONGBLOB
from sqlalchemy.sql import func
from app.database import Base


class BrandingAsset(Base):
    __tablename__ = "branding_assets"

    key = Column(String(50), primary_key=True)
    data = Column(LONGBLOB, nullable=True)
    content_type = Column(String(50), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
