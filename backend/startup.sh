#!/bin/sh

echo "Initializing database..."
python init_db.py 2>&1 || { echo "Failed to initialize database"; exit 1; }

echo "Running migrations..."
alembic upgrade head 2>&1 || echo "Note: Migrations may have already been applied"

echo "Starting server..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

