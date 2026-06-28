import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.production_step_definition import ProductionStepDefinition

router = APIRouter()


def _to_dict(d: ProductionStepDefinition) -> dict:
    return {
        "id": d.id,
        "name": d.name,
        "isActive": d.is_active,
        "createdAt": d.created_at.isoformat() if d.created_at else None,
        "updatedAt": d.updated_at.isoformat() if d.updated_at else None,
    }


class StepDefBody(BaseModel):
    name: str


@router.get("")
def list_definitions(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = (
        db.query(ProductionStepDefinition)
        .filter(ProductionStepDefinition.is_active == True)  # noqa: E712
        .order_by(ProductionStepDefinition.name)
        .all()
    )
    return [_to_dict(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_definition(
    body: StepDefBody,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    row = ProductionStepDefinition(id=str(uuid.uuid4()), name=name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_dict(row)


@router.put("/{def_id}")
def update_definition(
    def_id: str,
    body: StepDefBody,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    row = db.query(ProductionStepDefinition).filter(ProductionStepDefinition.id == def_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    row.name = name
    db.commit()
    db.refresh(row)
    return _to_dict(row)


@router.delete("/{def_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_definition(
    def_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    row = db.query(ProductionStepDefinition).filter(ProductionStepDefinition.id == def_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    # Soft delete: existing production steps that used this definition keep their
    # stored name, so removing it here does not break any existing data.
    row.is_active = False
    db.commit()
