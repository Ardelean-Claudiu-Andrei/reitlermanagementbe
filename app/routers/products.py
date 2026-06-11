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
from app.models.assembly import Assembly

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
    assemblySteps: list = []
    productionSteps: list = []
    notes: str = ""


class ProductUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[dict] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    basePrice: Optional[float] = None
    assemblyIds: Optional[list] = None
    partIds: Optional[list] = None
    assemblySteps: Optional[list] = None
    productionSteps: Optional[list] = None
    notes: Optional[str] = None


def product_to_dict(p: Product) -> dict:
    return {
        "id": p.id,
        "code": p.code,
        "name": p.name,
        "description": p.description or {"ro": "", "hu": "", "de": "", "en": ""},
        "category": p.category,
        "unit": p.unit,
        "basePrice": p.base_price,
        "assemblyIds": p.assembly_ids or [],
        "partIds": p.part_ids or [],
        "assemblySteps": p.assembly_steps or [],
        "productionSteps": p.production_steps or [],
        "notes": p.notes or "",
        "createdAt": p.created_at.isoformat() if p.created_at else None,
        "updatedAt": p.updated_at.isoformat() if p.updated_at else None,
    }


def _has_laser_cutting(product: Product, db: Session) -> bool:
    """Return True if product or any of its parts (direct or via assemblies) require laser cutting."""
    for part_id in (product.part_ids or []):
        part = db.query(Part).filter(Part.id == part_id).first()
        if part and part.requires_laser_cutting:
            return True
    for assembly_id in (product.assembly_ids or []):
        assembly = db.query(Assembly).filter(Assembly.id == assembly_id).first()
        if not assembly:
            continue
        for ap in (assembly.parts or []):
            part = db.query(Part).filter(Part.id == ap.get("partId")).first()
            if part and part.requires_laser_cutting:
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
    p = Product(
        code=body.code,
        name=body.name,
        description=body.description or {"ro": "", "hu": "", "de": "", "en": ""},
        category=body.category,
        unit=body.unit,
        base_price=body.basePrice,
        assembly_ids=body.assemblyIds or [],
        part_ids=body.partIds or [],
        assembly_steps=body.assemblySteps or [],
        production_steps=body.productionSteps or [],
        notes=body.notes,
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
    if body.assemblyIds is not None:
        p.assembly_ids = body.assemblyIds
    if body.partIds is not None:
        p.part_ids = body.partIds
    if body.assemblySteps is not None:
        p.assembly_steps = body.assemblySteps
    if body.productionSteps is not None:
        p.production_steps = body.productionSteps
    if body.notes is not None:
        p.notes = body.notes
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
