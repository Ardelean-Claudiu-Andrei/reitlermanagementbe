from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

router = APIRouter()


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "USER"


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


def user_to_dict(u: User) -> dict:
    role = "admin" if u.role == UserRole.ADMIN else "employee"
    return {
        "user": {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "status": "active" if u.is_active else "inactive",
        },
        "additionalInformation": {
            "userId": u.id,
            "role": role,
            "type": role,
        },
    }


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    users = db.query(User).order_by(User.name).all()
    return [user_to_dict(u) for u in users]


@router.get("/{user_id}")
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_dict(u)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already in use")
    role = UserRole.ADMIN if body.role.upper() == "ADMIN" else UserRole.USER
    user = User(
        name=body.name,
        email=body.email,
        hashed_password=AuthService.hash_password(body.password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_to_dict(user)


@router.put("/{user_id}")
def update_user(
    user_id: str,
    body: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if body.name is not None:
        u.name = body.name
    if body.email is not None:
        u.email = body.email
    if body.password is not None:
        u.hashed_password = AuthService.hash_password(body.password)
    if body.role is not None:
        u.role = UserRole.ADMIN if body.role.upper() == "ADMIN" else UserRole.USER
    if body.status is not None:
        u.is_active = body.status == "active"
    db.commit()
    db.refresh(u)
    return user_to_dict(u)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(u)
    db.commit()
