#!/bin/bash

# Azure App Service startup script for FastAPI
# This script is executed when the container starts

echo "Starting FastAPI application..."

# Install dependencies
pip install -r requirements.txt

# Run database migrations (create tables)
python -c "from models import Base, engine; Base.metadata.create_all(bind=engine); print('Database tables created successfully')"

# Start the FastAPI application with Gunicorn for production
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000