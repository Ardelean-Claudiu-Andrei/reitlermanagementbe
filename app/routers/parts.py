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
    code: Optional[str] = None
    name: str
    description: dict = {}
    category: str = ""
    unit: str = "buc"
    basePrice: float = 0.0
    minimumStock: float = 0.0
    quantity: float = 0.0
    requiredQuantity: int = 1
    location: str = ""
    physicalLocation: str = ""
    drawingLocation: str = ""
    requiresLaserCutting: bool = False
    weldingDrawingLocation: str = ""
    bendingDrawingLocation: str = ""
    cadLocation: str = ""
    technicalDrawingLocation: str = ""
    productionSteps: list = []
    notes: str = ""
    fileName: str = ""
    fileLocation: str = ""
    requiresPurchase: bool = False
    purchaseSupplier: str = ""
    purchasePrice: Optional[float] = None
    purchaseCurrency: str = "EUR"
    purchaseVatIncluded: bool = False
    purchaseVatRate: float = 21.0
    purchaseAgentContact: str = ""
    purchaseDetails: str = ""


class PartUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[dict] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    basePrice: Optional[float] = None
    minimumStock: Optional[float] = None
    quantity: Optional[float] = None
    requiredQuantity: Optional[int] = None
    location: Optional[str] = None
    physicalLocation: Optional[str] = None
    drawingLocation: Optional[str] = None
    requiresLaserCutting: Optional[bool] = None
    weldingDrawingLocation: Optional[str] = None
    bendingDrawingLocation: Optional[str] = None
    cadLocation: Optional[str] = None
    technicalDrawingLocation: Optional[str] = None
    productionSteps: Optional[list] = None
    notes: Optional[str] = None
    fileName: Optional[str] = None
    fileLocation: Optional[str] = None
    requiresPurchase: Optional[bool] = None
    purchaseSupplier: Optional[str] = None
    purchasePrice: Optional[float] = None
    purchaseCurrency: Optional[str] = None
    purchaseVatIncluded: Optional[bool] = None
    purchaseVatRate: Optional[float] = None
    purchaseAgentContact: Optional[str] = None
    purchaseDetails: Optional[str] = None


def part_to_dict(p: Part) -> dict:
    return {
        "id": p.id,
        "code": p.code or "",
        "name": p.name,
        "description": p.description or {"ro": "", "hu": "", "de": "", "en": ""},
        "category": p.category or "",
        "unit": p.unit,
        "basePrice": p.base_price,
        "minimumStock": p.minimum_stock or 0.0,
        "quantity": p.quantity or 0.0,
        "requiredQuantity": p.required_quantity or 1,
        "location": p.location or "",
        "physicalLocation": p.physical_location or "",
        "drawingLocation": p.drawing_location or "",
        "requiresLaserCutting": p.requires_laser_cutting or False,
        "weldingDrawingLocation": p.welding_drawing_location or "",
        "bendingDrawingLocation": p.bending_drawing_location or "",
        "cadLocation": p.cad_location or "",
        "technicalDrawingLocation": p.technical_drawing_location or "",
        "productionSteps": p.production_steps or [],
        "notes": p.notes or "",
        "fileName": p.file_name or "",
        "fileLocation": p.file_location or "",
        "requiresPurchase": p.requires_purchase or False,
        "purchaseSupplier": p.purchase_supplier or "",
        "purchasePrice": p.purchase_price,
        "purchaseCurrency": p.purchase_currency or "EUR",
        "purchaseVatIncluded": p.purchase_vat_included or False,
        "purchaseVatRate": p.purchase_vat_rate if p.purchase_vat_rate is not None else 21.0,
        "purchaseAgentContact": p.purchase_agent_contact or "",
        "purchaseDetails": p.purchase_details or "",
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
    if body.code and db.query(Part).filter(Part.code == body.code).first():
        raise HTTPException(status_code=400, detail="Part code already exists")
    p = Part(
        code=body.code or None,
        name=body.name,
        description=body.description or {"ro": "", "hu": "", "de": "", "en": ""},
        category=body.category,
        unit=body.unit,
        base_price=body.basePrice,
        minimum_stock=body.minimumStock,
        quantity=body.quantity,
        required_quantity=body.requiredQuantity,
        location=body.location,
        physical_location=body.physicalLocation,
        drawing_location=body.drawingLocation,
        requires_laser_cutting=body.requiresLaserCutting,
        welding_drawing_location=body.weldingDrawingLocation,
        bending_drawing_location=body.bendingDrawingLocation,
        cad_location=body.cadLocation,
        technical_drawing_location=body.technicalDrawingLocation,
        production_steps=body.productionSteps or [],
        notes=body.notes,
        file_name=body.fileName,
        file_location=body.fileLocation,
        requires_purchase=body.requiresPurchase,
        purchase_supplier=body.purchaseSupplier,
        purchase_price=body.purchasePrice,
        purchase_currency=body.purchaseCurrency,
        purchase_vat_included=body.purchaseVatIncluded,
        purchase_vat_rate=body.purchaseVatRate,
        purchase_agent_contact=body.purchaseAgentContact,
        purchase_details=body.purchaseDetails,
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
    if body.code is not None:
        if body.code and db.query(Part).filter(Part.code == body.code, Part.id != part_id).first():
            raise HTTPException(status_code=400, detail="Part code already exists")
        p.code = body.code or None
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
    if body.requiredQuantity is not None:
        p.required_quantity = body.requiredQuantity
    if body.location is not None:
        p.location = body.location
    if body.physicalLocation is not None:
        p.physical_location = body.physicalLocation
    if body.drawingLocation is not None:
        p.drawing_location = body.drawingLocation
    if body.requiresLaserCutting is not None:
        p.requires_laser_cutting = body.requiresLaserCutting
    if body.weldingDrawingLocation is not None:
        p.welding_drawing_location = body.weldingDrawingLocation
    if body.bendingDrawingLocation is not None:
        p.bending_drawing_location = body.bendingDrawingLocation
    if body.cadLocation is not None:
        p.cad_location = body.cadLocation
    if body.technicalDrawingLocation is not None:
        p.technical_drawing_location = body.technicalDrawingLocation
    if body.productionSteps is not None:
        p.production_steps = body.productionSteps
    if body.notes is not None:
        p.notes = body.notes
    if body.fileName is not None:
        p.file_name = body.fileName
    if body.fileLocation is not None:
        p.file_location = body.fileLocation
    if body.requiresPurchase is not None:
        p.requires_purchase = body.requiresPurchase
    if body.purchaseSupplier is not None:
        p.purchase_supplier = body.purchaseSupplier
    if body.purchasePrice is not None:
        p.purchase_price = body.purchasePrice
    if body.purchaseCurrency is not None:
        p.purchase_currency = body.purchaseCurrency
    if body.purchaseVatIncluded is not None:
        p.purchase_vat_included = body.purchaseVatIncluded
    if body.purchaseVatRate is not None:
        p.purchase_vat_rate = body.purchaseVatRate
    if body.purchaseAgentContact is not None:
        p.purchase_agent_contact = body.purchaseAgentContact
    if body.purchaseDetails is not None:
        p.purchase_details = body.purchaseDetails
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
