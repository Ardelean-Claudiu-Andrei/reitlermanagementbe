from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.part import Part

router = APIRouter()


class PartCreate(BaseModel):
    name: str
    description: dict = {}
    fileName: str = ""
    fileLocation: str = ""
    unit: str = "buc"
    basePrice: float = 0.0


class PartUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[dict] = None
    fileName: Optional[str] = None
    fileLocation: Optional[str] = None
    unit: Optional[str] = None
    basePrice: Optional[float] = None


def part_to_dict(p: Part) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description or {"ro": "", "hu": "", "de": "", "en": ""},
        "fileName": p.file_name or "",
        "fileLocation": p.file_location or "",
        "unit": p.unit,
        "basePrice": p.base_price,
        "createdAt": p.created_at.isoformat() if p.created_at else None,
        "updatedAt": p.updated_at.isoformat() if p.updated_at else None,
    }


@router.get("")
def list_parts(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    parts = db.query(Part).order_by(Part.name).all()
    return [part_to_dict(p) for p in parts]


@router.get("/{part_id}")
def get_part(
    part_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Part).filter(Part.id == part_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Part not found")
    return part_to_dict(p)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_part(
    body: PartCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = Part(
        name=body.name,
        description=body.description or {"ro": "", "hu": "", "de": "", "en": ""},
        file_name=body.fileName,
        file_location=body.fileLocation,
        unit=body.unit,
        base_price=body.basePrice,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return part_to_dict(p)


@router.put("/{part_id}")
def update_part(
    part_id: str,
    body: PartUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Part).filter(Part.id == part_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Part not found")
    if body.name is not None:
        p.name = body.name
    if body.description is not None:
        p.description = body.description
    if body.fileName is not None:
        p.file_name = body.fileName
    if body.fileLocation is not None:
        p.file_location = body.fileLocation
    if body.unit is not None:
        p.unit = body.unit
    if body.basePrice is not None:
        p.base_price = body.basePrice
    db.commit()
    db.refresh(p)
    return part_to_dict(p)


@router.delete("/{part_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_part(
    part_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Part).filter(Part.id == part_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Part not found")
    db.delete(p)
    db.commit()
