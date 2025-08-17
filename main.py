import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from tempfile import NamedTemporaryFile
import tempfile
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, onboarding
from routers.talk import router as talk_router

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI(title="TANABOTA API", version="1.0.0")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your-secret-key-change-in-production"),
    max_age=int(os.getenv("SESSION_MAX_AGE", "3600"))
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

app.include_router(talk_router)

app.include_router(onboarding.router)

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時のデモデータシード処理"""
    
    # SEED_DEMO_DATAがtrueの場合のみ実行
    should_seed = os.getenv("SEED_DEMO_DATA", "false").lower() in ["true", "1", "yes"]
    
    if should_seed:
        print("🌱 デモデータのシード処理を開始します...")
        
        try:
            # FORCE_SEEDがfalseの場合は既存データをチェック
            force_seed = os.getenv("FORCE_SEED", "false").lower() in ["true", "1", "yes"]
            
            if not force_seed and has_existing_data():
                print("ℹ️  デモデータは既に存在します。スキップします。")
                print("   強制実行したい場合は FORCE_SEED=true を設定してください。")
                return
            
            # シード実行
            from seeds import seed_sample_data
            seed_sample_data(clear_existing=True)
            
            print("✅ デモデータのシードが完了しました")
            
        except Exception as e:
            print(f"❌ デモデータのシード処理でエラーが発生しました: {e}")

def has_existing_data():
    """既存データの存在チェック"""
    try:
        from database import SessionLocal
        from models import User
        
        db = SessionLocal()
        # サンプルユーザー（ID=1）の存在確認
        existing_user = db.query(User).filter(User.id == 1).first()
        db.close()
        
        return existing_user is not None
        
    except Exception as e:
        print(f"⚠️  データ存在チェックでエラー: {e}")
        return False



@app.get("/")
def read_root():
    return {"message": "User Authentication API is running"}


# Azure App Service will use startup.py instead of this
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)