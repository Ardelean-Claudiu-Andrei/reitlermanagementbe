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
    firstName: str
    lastName: str
    email: str
    password: str
    role: str = "USER"


class UserUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class ProfileUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None
    currentPassword: Optional[str] = None
    newPassword: Optional[str] = None


def user_to_dict(u: User) -> dict:
    role = "admin" if u.role == UserRole.ADMIN else "employee"
    first = u.first_name or ""
    last = u.last_name or ""
    full_name = f"{first} {last}".strip() or u.name
    return {
        "user": {
            "id": u.id,
            "firstName": first,
            "lastName": last,
            "name": full_name,
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
    users = db.query(User).order_by(User.last_name, User.first_name).all()
    return [user_to_dict(u) for u in users]


@router.get("/profile")
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return user_to_dict(current_user)


@router.put("/profile")
def update_profile(
    body: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.firstName is not None:
        current_user.first_name = body.firstName
        current_user.name = f"{body.firstName} {current_user.last_name or ''}".strip()
    if body.lastName is not None:
        current_user.last_name = body.lastName
        current_user.name = f"{current_user.first_name or ''} {body.lastName}".strip()
    if body.email is not None:
        existing = db.query(User).filter(User.email == body.email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = body.email
    if body.newPassword:
        if body.currentPassword and not AuthService.verify_password(body.currentPassword, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        current_user.hashed_password = AuthService.hash_password(body.newPassword)
    db.commit()
    db.refresh(current_user)
    return user_to_dict(current_user)


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
    full_name = f"{body.firstName} {body.lastName}".strip()
    user = User(
        first_name=body.firstName,
        last_name=body.lastName,
        name=full_name,
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
    if body.firstName is not None:
        u.first_name = body.firstName
    if body.lastName is not None:
        u.last_name = body.lastName
    # Keep name in sync
    u.name = f"{u.first_name or ''} {u.last_name or ''}".strip() or u.name
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
