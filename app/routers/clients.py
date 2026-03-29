from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.client import Client

router = APIRouter()


class ClientCreate(BaseModel):
    name: str
    contactPerson: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    cui: str = ""


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    contactPerson: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    cui: Optional[str] = None


def client_to_dict(c: Client) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "contactPerson": c.contact_person or "",
        "email": c.email or "",
        "phone": c.phone or "",
        "address": c.address or "",
        "cui": c.cui or "",
        "createdAt": c.created_at.isoformat() if c.created_at else None,
        "updatedAt": c.updated_at.isoformat() if c.updated_at else None,
    }


@router.get("")
def list_clients(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    clients = db.query(Client).order_by(Client.name).all()
    return [client_to_dict(c) for c in clients]


@router.get("/{client_id}")
def get_client(
    client_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    c = db.query(Client).filter(Client.id == client_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Client not found")
    return client_to_dict(c)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_client(
    body: ClientCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    c = Client(
        name=body.name,
        contact_person=body.contactPerson,
        email=body.email,
        phone=body.phone,
        address=body.address,
        cui=body.cui,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return client_to_dict(c)


@router.put("/{client_id}")
def update_client(
    client_id: str,
    body: ClientUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    c = db.query(Client).filter(Client.id == client_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Client not found")
    if body.name is not None:
        c.name = body.name
    if body.contactPerson is not None:
        c.contact_person = body.contactPerson
    if body.email is not None:
        c.email = body.email
    if body.phone is not None:
        c.phone = body.phone
    if body.address is not None:
        c.address = body.address
    if body.cui is not None:
        c.cui = body.cui
    db.commit()
    db.refresh(c)
    return client_to_dict(c)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    c = db.query(Client).filter(Client.id == client_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(c)
    db.commit()
