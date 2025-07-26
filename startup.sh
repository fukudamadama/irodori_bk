#!/bin/bash

# Azure App Service startup script for Python
echo "Starting FastAPI application..."

# Set environment variables
export PYTHONPATH="/home/site/wwwroot:$PYTHONPATH"

# Run the application
python /home/site/wwwroot/startup.py