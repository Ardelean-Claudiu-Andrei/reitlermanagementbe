from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.assembly import Assembly

router = APIRouter()


class AssemblyCreate(BaseModel):
    code: str
    name: str
    description: dict = {}
    parts: list = []
    notes: str = ""


class AssemblyUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[dict] = None
    parts: Optional[list] = None
    notes: Optional[str] = None


def assembly_to_dict(a: Assembly) -> dict:
    return {
        "id": a.id,
        "code": a.code,
        "name": a.name,
        "description": a.description or {"ro": "", "hu": "", "de": "", "en": ""},
        "parts": a.parts or [],
        "notes": a.notes or "",
        "createdAt": a.created_at.isoformat() if a.created_at else None,
        "updatedAt": a.updated_at.isoformat() if a.updated_at else None,
    }


@router.get("")
def list_assemblies(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    assemblies = db.query(Assembly).order_by(Assembly.name).all()
    return [assembly_to_dict(a) for a in assemblies]


@router.get("/{assembly_id}")
def get_assembly(
    assembly_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    a = db.query(Assembly).filter(Assembly.id == assembly_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assembly not found")
    return assembly_to_dict(a)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_assembly(
    body: AssemblyCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if db.query(Assembly).filter(Assembly.code == body.code).first():
        raise HTTPException(status_code=400, detail="Assembly code already exists")
    a = Assembly(
        code=body.code,
        name=body.name,
        description=body.description or {"ro": "", "hu": "", "de": "", "en": ""},
        parts=body.parts or [],
        notes=body.notes,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return assembly_to_dict(a)


@router.put("/{assembly_id}")
def update_assembly(
    assembly_id: str,
    body: AssemblyUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    a = db.query(Assembly).filter(Assembly.id == assembly_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assembly not found")
    if body.code is not None:
        a.code = body.code
    if body.name is not None:
        a.name = body.name
    if body.description is not None:
        a.description = body.description
    if body.parts is not None:
        a.parts = body.parts
    if body.notes is not None:
        a.notes = body.notes
    db.commit()
    db.refresh(a)
    return assembly_to_dict(a)


@router.delete("/{assembly_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assembly(
    assembly_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    a = db.query(Assembly).filter(Assembly.id == assembly_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assembly not found")
    db.delete(a)
    db.commit()
