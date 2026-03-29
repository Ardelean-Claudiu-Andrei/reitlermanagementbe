from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.inventory import InventoryItem

router = APIRouter()


class InventoryCreate(BaseModel):
    type: str  # "product" or "part"
    itemId: str
    quantity: float = 0.0
    minStock: float = 0.0
    location: str = ""


class InventoryUpdate(BaseModel):
    quantity: Optional[float] = None
    minStock: Optional[float] = None
    location: Optional[str] = None


def inventory_to_dict(i: InventoryItem) -> dict:
    return {
        "id": i.id,
        "type": i.type,
        "itemId": i.item_id,
        "quantity": i.quantity,
        "minStock": i.min_stock,
        "location": i.location or "",
        "updatedAt": i.updated_at.isoformat() if i.updated_at else None,
    }


@router.get("")
def list_inventory(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items = db.query(InventoryItem).all()
    return [inventory_to_dict(i) for i in items]


@router.get("/{item_id}")
def get_inventory_item(
    item_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    i = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not i:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return inventory_to_dict(i)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_inventory_item(
    body: InventoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    i = InventoryItem(
        type=body.type,
        item_id=body.itemId,
        quantity=body.quantity,
        min_stock=body.minStock,
        location=body.location,
    )
    db.add(i)
    db.commit()
    db.refresh(i)
    return inventory_to_dict(i)


@router.put("/{item_id}")
def update_inventory_item(
    item_id: str,
    body: InventoryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    i = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not i:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    if body.quantity is not None:
        i.quantity = body.quantity
    if body.minStock is not None:
        i.min_stock = body.minStock
    if body.location is not None:
        i.location = body.location
    db.commit()
    db.refresh(i)
    return inventory_to_dict(i)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(
    item_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    i = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not i:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    db.delete(i)
    db.commit()
