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
    category: str = ""
    unit: str = "buc"
    basePrice: float = 0.0
    minimumStock: float = 0.0
    quantity: float = 0.0
    location: str = ""
    notes: str = ""
    fileName: str = ""
    fileLocation: str = ""


class PartUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[dict] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    basePrice: Optional[float] = None
    minimumStock: Optional[float] = None
    quantity: Optional[float] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    fileName: Optional[str] = None
    fileLocation: Optional[str] = None


def part_to_dict(p: Part) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description or {"ro": "", "hu": "", "de": "", "en": ""},
        "category": p.category or "",
        "unit": p.unit,
        "basePrice": p.base_price,
        "minimumStock": p.minimum_stock or 0.0,
        "quantity": p.quantity or 0.0,
        "location": p.location or "",
        "notes": p.notes or "",
        "fileName": p.file_name or "",
        "fileLocation": p.file_location or "",
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
        category=body.category,
        unit=body.unit,
        base_price=body.basePrice,
        minimum_stock=body.minimumStock,
        quantity=body.quantity,
        location=body.location,
        notes=body.notes,
        file_name=body.fileName,
        file_location=body.fileLocation,
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
    if body.category is not None:
        p.category = body.category
    if body.unit is not None:
        p.unit = body.unit
    if body.basePrice is not None:
        p.base_price = body.basePrice
    if body.minimumStock is not None:
        p.minimum_stock = body.minimumStock
    if body.quantity is not None:
        p.quantity = body.quantity
    if body.location is not None:
        p.location = body.location
    if body.notes is not None:
        p.notes = body.notes
    if body.fileName is not None:
        p.file_name = body.fileName
    if body.fileLocation is not None:
        p.file_location = body.fileLocation
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
