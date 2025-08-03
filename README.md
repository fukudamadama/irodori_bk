# IRODORI Backend (FastAPI)

User authentication API using FastAPI, SQLAlchemy, and session-based authentication.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

## シードデータ

アプリケーション起動時に自動でサンプルデータを投入できます。

### 設定方法

環境変数でシード動作を制御：

```bash
# .env ファイルまたは環境変数で設定
SEED_DEMO_DATA=true          # シードを実行するか
FORCE_SEED=false             # 既存データがあっても強制実行するか
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

### Auth

- `POST /register` - User registration
- `POST /login` - User login
- `GET /logout` - User logout
- `GET /me` - Get current user info

### Onboarding

- `POST /onboarding/preference` - 単一のユーザー傾向を保存
- `POST /onboarding/preferences` - 複数のユーザー傾向のリストを一括で保存
- `GET /onboarding/preferences` - 特定のユーザーに紐づくすべてのユーザー傾向を一括で取得
