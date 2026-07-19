from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.part import Part

router = APIRouter()


class ProductCreate(BaseModel):
    code: str
    name: str
    description: dict = {}
    category: str = "other"
    unit: str = "buc"
    basePrice: float = 0.0
    assemblyIds: list = []
    partIds: list = []
    productAssemblies: list = []  # [{assemblyId, quantity}]
    productParts: list = []       # [{partId, quantity}]
    assemblySteps: list = []
    productionSteps: list = []
    notes: str = ""
    requiresPurchase: bool = False
    purchaseSupplier: str = ""
    purchasePrice: Optional[float] = None
    purchaseCurrency: str = "EUR"
    purchaseVatIncluded: bool = False
    purchaseVatRate: float = 21.0
    purchaseAgentContact: str = ""
    purchaseDetails: str = ""


class ProductUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[dict] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    basePrice: Optional[float] = None
    assemblyIds: Optional[list] = None
    partIds: Optional[list] = None
    productAssemblies: Optional[list] = None  # [{assemblyId, quantity}]
    productParts: Optional[list] = None       # [{partId, quantity}]
    assemblySteps: Optional[list] = None
    productionSteps: Optional[list] = None
    notes: Optional[str] = None
    requiresPurchase: Optional[bool] = None
    purchaseSupplier: Optional[str] = None
    purchasePrice: Optional[float] = None
    purchaseCurrency: Optional[str] = None
    purchaseVatIncluded: Optional[bool] = None
    purchaseVatRate: Optional[float] = None
    purchaseAgentContact: Optional[str] = None
    purchaseDetails: Optional[str] = None


def product_to_dict(p: Product) -> dict:
    # Derive productAssemblies/productParts, falling back to legacy assemblyIds/partIds with qty=1
    product_assemblies: list = p.product_assemblies or []
    product_parts: list = p.product_parts or []

    if not product_assemblies and p.assembly_ids:
        product_assemblies = [{"assemblyId": aid, "quantity": 1} for aid in p.assembly_ids]
    if not product_parts and p.part_ids:
        product_parts = [{"partId": pid, "quantity": 1} for pid in p.part_ids]

    assembly_ids = [a["assemblyId"] for a in product_assemblies if a.get("assemblyId")]
    part_ids = [pt["partId"] for pt in product_parts if pt.get("partId")]

    return {
        "id": p.id,
        "code": p.code,
        "name": p.name,
        "description": p.description or {"ro": "", "hu": "", "de": "", "en": ""},
        "category": p.category,
        "unit": p.unit,
        "basePrice": p.base_price,
        "assemblyIds": assembly_ids,
        "partIds": part_ids,
        "productAssemblies": product_assemblies,
        "productParts": product_parts,
        "assemblySteps": p.assembly_steps or [],
        "productionSteps": p.production_steps or [],
        "notes": p.notes or "",
        "requiresPurchase": bool(p.requires_purchase) if p.requires_purchase is not None else False,
        "purchaseSupplier": p.purchase_supplier or "",
        "purchasePrice": p.purchase_price,
        "purchaseCurrency": p.purchase_currency or "EUR",
        "purchaseVatIncluded": bool(p.purchase_vat_included) if p.purchase_vat_included is not None else False,
        "purchaseVatRate": p.purchase_vat_rate if p.purchase_vat_rate is not None else 21.0,
        "purchaseAgentContact": p.purchase_agent_contact or "",
        "purchaseDetails": p.purchase_details or "",
        "createdAt": p.created_at.isoformat() if p.created_at else None,
        "updatedAt": p.updated_at.isoformat() if p.updated_at else None,
    }


def _get_assembly_ids(product: Product) -> list:
    """Return assembly IDs from new product_assemblies or fall back to legacy assembly_ids."""
    if product.product_assemblies:
        return [a["assemblyId"] for a in product.product_assemblies if a.get("assemblyId")]
    return product.assembly_ids or []


def _get_part_ids(product: Product) -> list:
    """Return part IDs from new product_parts or fall back to legacy part_ids."""
    if product.product_parts:
        return [pt["partId"] for pt in product.product_parts if pt.get("partId")]
    return product.part_ids or []


def _has_laser_cutting(product: Product, db: Session) -> bool:
    """Return True if product or any of its parts (direct or via assemblies) require laser cutting."""
    from app.services.assembly_tree import assembly_requires_laser
    for part_id in _get_part_ids(product):
        part = db.query(Part).filter(Part.id == part_id).first()
        if part and part.requires_laser_cutting:
            return True
    for assembly_id in _get_assembly_ids(product):
        if assembly_requires_laser(assembly_id, db):
            return True
    return False


@router.get("")
def list_products(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    products = db.query(Product).filter(Product.is_active.isnot(False)).order_by(Product.name).all()
    result = []
    for p in products:
        d = product_to_dict(p)
        d["hasLaserCutting"] = _has_laser_cutting(p, db)
        result.append(d)
    return result


@router.get("/{product_id}")
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    result = product_to_dict(p)
    result["hasLaserCutting"] = _has_laser_cutting(p, db)
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
def create_product(
    body: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if db.query(Product).filter(Product.code == body.code).first():
        raise HTTPException(status_code=400, detail="Product code already exists")
    product_assemblies = body.productAssemblies or []
    product_parts = body.productParts or []
    # Derive legacy assemblyIds/partIds from new format if provided, else use directly
    assembly_ids = body.assemblyIds or [a["assemblyId"] for a in product_assemblies if a.get("assemblyId")]
    part_ids = body.partIds or [pt["partId"] for pt in product_parts if pt.get("partId")]

    p = Product(
        code=body.code,
        name=body.name,
        description=body.description or {"ro": "", "hu": "", "de": "", "en": ""},
        category=body.category,
        unit=body.unit,
        base_price=body.basePrice,
        assembly_ids=assembly_ids,
        part_ids=part_ids,
        product_assemblies=product_assemblies,
        product_parts=product_parts,
        assembly_steps=body.assemblySteps or [],
        production_steps=body.productionSteps or [],
        notes=body.notes,
        requires_purchase=body.requiresPurchase,
        purchase_supplier=body.purchaseSupplier,
        purchase_price=body.purchasePrice,
        purchase_currency=body.purchaseCurrency,
        purchase_vat_included=body.purchaseVatIncluded,
        purchase_vat_rate=body.purchaseVatRate,
        purchase_agent_contact=body.purchaseAgentContact,
        purchase_details=body.purchaseDetails or None,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return product_to_dict(p)


@router.put("/{product_id}")
def update_product(
    product_id: str,
    body: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    if body.code is not None:
        p.code = body.code
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
    if body.productAssemblies is not None:
        p.product_assemblies = body.productAssemblies
        p.assembly_ids = [a["assemblyId"] for a in body.productAssemblies if a.get("assemblyId")]
    elif body.assemblyIds is not None:
        p.assembly_ids = body.assemblyIds
    if body.productParts is not None:
        p.product_parts = body.productParts
        p.part_ids = [pt["partId"] for pt in body.productParts if pt.get("partId")]
    elif body.partIds is not None:
        p.part_ids = body.partIds
    if body.assemblySteps is not None:
        p.assembly_steps = body.assemblySteps
    if body.productionSteps is not None:
        p.production_steps = body.productionSteps
    if body.notes is not None:
        p.notes = body.notes
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
        p.purchase_details = body.purchaseDetails or None
    db.commit()
    db.refresh(p)
    return product_to_dict(p)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    p.is_active = False
    db.commit()


@router.get("/{product_id}/export-production-steps")
def export_production_steps_pdf(
    product_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")

    from app.services.steps_pdf_service import generate_product_steps_pdf
    pdf_bytes = generate_product_steps_pdf(p, db)

    filename = f"pasi-productie-{p.code}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{product_id}/laser-cutting-pdf")
def export_laser_cutting_pdf(
    product_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    if not _has_laser_cutting(p, db):
        raise HTTPException(status_code=400, detail="This product has no laser cutting parts")

    from app.services.laser_cutting_pdf_service import generate_laser_cutting_pdf
    pdf_bytes = generate_laser_cutting_pdf(p, db)

    filename = f"laser-cutting-{p.code}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
