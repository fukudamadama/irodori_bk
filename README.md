# IRODORI Backend (FastAPI)

User authentication API using FastAPI, SQLAlchemy, and session-based authentication.

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Azure Deployment

This repository includes GitHub Actions workflow for automatic deployment to Azure App Service.

### Required Secrets
- `AZURE_WEBAPP_NAME` - Your App Service name
- `AZURE_WEBAPP_PUBLISH_PROFILE` - Download from Azure Portal

### Environment Variables (in Azure)
- `SECRET_KEY` - Session secret key
- `ALLOWED_ORIGINS` - Frontend URL (comma-separated)
- `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` - Database config

## Endpoints

- `POST /register` - User registration
- `POST /login` - User login
- `GET /logout` - User logout  
- `GET /me` - Get current user info