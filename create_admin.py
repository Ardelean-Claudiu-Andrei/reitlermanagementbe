import os
import sys

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

admin_email = os.environ.get("ADMIN_EMAIL", "").strip()
admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()

if not admin_email or not admin_password:
    print("Error: ADMIN_EMAIL and ADMIN_PASSWORD environment variables are required.")
    print("Usage: docker compose exec backend env ADMIN_EMAIL=you@example.com ADMIN_PASSWORD=secret python -m create_admin")
    sys.exit(1)

db = SessionLocal()

existing = db.query(User).filter(User.email == admin_email).first()
if existing:
    print(f"Admin with email '{admin_email}' already exists!")
else:
    admin = User(
        name="Administrator",
        email=admin_email,
        hashed_password=AuthService.hash_password(admin_password),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    print(f"Admin '{admin_email}' created successfully!")

db.close()
