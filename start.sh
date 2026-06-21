#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding initial admin user..."
python -m app.seed_admin || echo "WARNING: seed_admin failed (non-fatal), continuing..."

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
