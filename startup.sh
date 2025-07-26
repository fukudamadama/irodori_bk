#!/bin/bash
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo "Starting gunicorn..."
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app