"""
Idempotent admin seed script.

Usage:
    python -m app.seed_admin

Reads SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD from the environment (falls back
to safe defaults). Creates the admin user only if the email does not exist yet.
Safe to call on every deploy.
"""

import os
import logging

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

SEED_EMAIL    = os.environ.get("SEED_ADMIN_EMAIL",    "administrator@reitler.ro")
SEED_PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD", "Test12345ReitlerBigBoss")


def seed() -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == SEED_EMAIL).first()
        if existing:
            logger.info("Seed admin already exists (%s) — skipping.", SEED_EMAIL)
            return

        admin = User(
            first_name="Administrator",
            last_name="Reitler",
            name="Administrator Reitler",
            email=SEED_EMAIL,
            hashed_password=AuthService.hash_password(SEED_PASSWORD),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        logger.info("Seed admin created: %s", SEED_EMAIL)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    seed()
