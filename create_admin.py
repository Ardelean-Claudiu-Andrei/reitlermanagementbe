from app.database import SessionLocal
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

db = SessionLocal()

existing = db.query(User).filter(User.email == "admin@reitler.ro").first()
if existing:
    print("Admin există deja!")
else:
    admin = User(
        name="Administrator",
        email="admin@reitler.ro",
        hashed_password=AuthService.hash_password("admin123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(admin)
    db.commit()
    print("Admin creat cu succes!")
db.close()