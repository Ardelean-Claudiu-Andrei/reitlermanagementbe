import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import io
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.quote import Quote
from app.models.client import Client
from app.models.product import Product
from app.routers.settings import get_asset_data_uri
from app.services.pdf_service import generate_offer_pdf
from app.services.excel_service import generate_offer_excel

router = APIRouter()


class QuoteCreate(BaseModel):
    name: str
    description: str = ""
    companyId: Optional[str] = None
    status: str = "draft"
    validity: str = ""
    deliveryTimeWeeks: int = 4
    items: list = []
    installation: float = 0.0
    notes: str = ""


class QuoteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    companyId: Optional[str] = None
    status: Optional[str] = None
    validity: Optional[str] = None
    deliveryTimeWeeks: Optional[int] = None
    items: Optional[list] = None
    installation: Optional[float] = None
    notes: Optional[str] = None


class StatusUpdate(BaseModel):
    status: str


def quote_to_dict(q: Quote) -> dict:
    return {
        "id": q.id,
        "name": q.name,
        "description": q.description or "",
        "companyId": q.company_id,
        "status": q.status,
        "validity": q.validity or "",
        "deliveryTimeWeeks": q.delivery_time_weeks,
        "items": q.items or [],
        "installation": q.installation or 0.0,
        "notes": q.notes or "",
        "createdAt": q.created_at.isoformat() if q.created_at else None,
        "updatedAt": q.updated_at.isoformat() if q.updated_at else None,
    }


@router.get("")
def list_quotes(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    quotes = db.query(Quote).order_by(Quote.created_at.desc()).all()
    return [quote_to_dict(q) for q in quotes]


@router.get("/{quote_id}")
def get_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Quote).filter(Quote.id == quote_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote_to_dict(q)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_quote(
    body: QuoteCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = Quote(
        name=body.name,
        description=body.description,
        company_id=body.companyId,
        status=body.status,
        validity=body.validity,
        delivery_time_weeks=body.deliveryTimeWeeks,
        items=body.items or [],
        installation=body.installation,
        notes=body.notes,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return quote_to_dict(q)


@router.put("/{quote_id}")
def update_quote(
    quote_id: str,
    body: QuoteUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Quote).filter(Quote.id == quote_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Quote not found")
    if body.name is not None:
        q.name = body.name
    if body.description is not None:
        q.description = body.description
    if body.companyId is not None:
        q.company_id = body.companyId
    if body.status is not None:
        q.status = body.status
    if body.validity is not None:
        q.validity = body.validity
    if body.deliveryTimeWeeks is not None:
        q.delivery_time_weeks = body.deliveryTimeWeeks
    if body.items is not None:
        q.items = body.items
    if body.installation is not None:
        q.installation = body.installation
    if body.notes is not None:
        q.notes = body.notes
    db.commit()
    db.refresh(q)
    return quote_to_dict(q)


@router.patch("/{quote_id}/status")
def update_quote_status(
    quote_id: str,
    body: StatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Quote).filter(Quote.id == quote_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Quote not found")
    q.status = body.status
    db.commit()
    db.refresh(q)
    return quote_to_dict(q)


@router.post("/{quote_id}/duplicate", status_code=status.HTTP_201_CREATED)
def duplicate_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    original = db.query(Quote).filter(Quote.id == quote_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Quote not found")
    copy = Quote(
        name=f"{original.name} (Copy)",
        description=original.description,
        company_id=original.company_id,
        status="draft",
        validity=original.validity,
        delivery_time_weeks=original.delivery_time_weeks,
        items=list(original.items) if original.items else [],
        installation=original.installation,
        notes=original.notes,
    )
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return quote_to_dict(copy)


@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Quote).filter(Quote.id == quote_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Quote not found")
    db.delete(q)
    db.commit()


@router.get("/{quote_id}/generate-pdf")
def generate_quote_pdf(
    quote_id: str,
    lang: str = Query(default="ro", pattern="^(ro|hu|de|en)$"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q, company, products = _load_quote_context(quote_id, db)
    logo_uri = get_asset_data_uri(db, "header")
    signature_uri = get_asset_data_uri(db, "signature")

    pdf_bytes = generate_offer_pdf(
        quote=quote_to_dict(q),
        company=company,
        products=products,
        lang=lang,
        logo_data_uri=logo_uri,
        signature_data_uri=signature_uri,
    )

    filename = f"offer-{quote_id[:8]}-{lang}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _load_quote_context(quote_id: str, db: Session):
    """Shared helper: load quote + company + products from DB."""
    q = db.query(Quote).filter(Quote.id == quote_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Quote not found")

    company = None
    if q.company_id:
        client = db.query(Client).filter(Client.id == q.company_id).first()
        if client:
            company = {"id": client.id, "name": client.name}

    product_ids = {item.get("productId") for item in (q.items or []) if item.get("productId")}
    db_products = db.query(Product).filter(Product.id.in_(product_ids)).all() if product_ids else []
    products = [
        {"id": p.id, "name": p.name, "description": p.description or {}}
        for p in db_products
    ]
    return q, company, products


@router.get("/{quote_id}/generate-excel")
def generate_quote_excel(
    quote_id: str,
    lang: str = Query(default="ro", pattern="^(ro|hu|de|en)$"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q, company, products = _load_quote_context(quote_id, db)
    logo_uri = get_asset_data_uri(db, "header")
    signature_uri = get_asset_data_uri(db, "signature")

    xlsx_bytes = generate_offer_excel(
        quote=quote_to_dict(q),
        company=company,
        products=products,
        lang=lang,
        logo_data_uri=logo_uri,
        signature_data_uri=signature_uri,
    )

    filename = f"offer-{quote_id[:8]}-{lang}.xlsx"
    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
