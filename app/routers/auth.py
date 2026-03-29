from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import AuthService
from app.dependencies import get_current_user
from app.models.user import User, UserRole

router = APIRouter()


def user_info(u: User) -> dict:
    first = u.first_name or ""
    last = u.last_name or ""
    return {
        "id": u.id,
        "firstName": first,
        "lastName": last,
        "name": f"{first} {last}".strip() or u.name,
        "email": u.email,
        "role": "admin" if u.role == UserRole.ADMIN else "employee",
    }


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = AuthService.authenticate_user(form_data.username, form_data.password, db)
    access_token = AuthService.create_access_token({"sub": str(user.id)})
    refresh_token = AuthService.create_refresh_token({"sub": str(user.id)})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_info(user),
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return user_info(current_user)
