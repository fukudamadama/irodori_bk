FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create database tables on startup
RUN echo '#!/bin/bash\npython -c "from models import Base, engine; Base.metadata.create_all(bind=engine); print(\"Database tables created successfully\")" || echo "Database tables already exist"\npython main.py' > /app/start.sh
RUN chmod +x /app/start.sh

# Expose port
EXPOSE 8000

# Start the application
CMD ["./start.sh"]