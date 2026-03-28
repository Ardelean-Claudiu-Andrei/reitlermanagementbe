from app.database import SessionLocal
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

db = SessionLocal()

existing = db.query(User).filter(User.email == "").first()
if existing:
    print("Admin există deja!")
else:
    admin = User(
        name="Administrator",
        email="",
        hashed_password=AuthService.hash_password(""),
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(admin)
    db.commit()
    print("Admin creat cu succes!")
db.close()
