from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import get_db, User, hash_password
from datetime import date, datetime
import uuid

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    """
    MySQL の users テーブルから全ユーザー一覧を取得するテスト用エンドポイント
    """
    try:
        users = db.query(User).all()
        
        # 結果をJSON形式で返すために辞書形式に変換
        users_list = []
        for user in users:
            user_dict = {
                "id": user.id,
                "last_name": user.last_name,
                "first_name": user.first_name,
                "email": user.email,
                "birth_date": user.birth_date.isoformat() if user.birth_date else None,
                "postal_code": user.postal_code,
                "address": user.address,
                "phone_number": user.phone_number,
                "occupation": user.occupation,
                "company_name": user.company_name,
                "password_hash": user.password_hash[:20] + "..." if user.password_hash else None,  # セキュリティのため一部のみ表示
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
            users_list.append(user_dict)
        
        return {
            "status": "success",
            "total_users": len(users_list),
            "users": users_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/create-test-user")
def create_test_user(db: Session = Depends(get_db)):
    """
    テスト用ユーザーを1件作成するエンドポイント
    IDやメールアドレスの衝突を避けるためUUIDを使用
    """
    try:
        # 重複を避けるためランダムなUUIDを生成
        unique_id = str(uuid.uuid4())[:8]
        test_email = f"test-user-{unique_id}@example.com"
        
        # 既存ユーザーをチェック
        existing_user = db.query(User).filter(User.email == test_email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Test user already exists")
        
        # テストユーザーを作成
        test_user = User(
            last_name="田中",
            first_name="太郎",
            email=test_email,
            birth_date=date(1990, 1, 1),
            postal_code="123-4567",
            address=f"東京都新宿区テスト町1-{unique_id[:3]}番地",
            phone_number="09012345678",
            occupation="テストエンジニア",
            company_name=f"テスト株式会社-{unique_id[:4]}",
            password_hash=hash_password("testpassword123")
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        return {
            "status": "success",
            "message": "Test user created successfully",
            "user": {
                "id": test_user.id,
                "email": test_user.email,
                "name": f"{test_user.last_name} {test_user.first_name}",
                "created_at": test_user.created_at.isoformat()
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create test user: {str(e)}")

@router.get("/db-info")
def get_database_info(db: Session = Depends(get_db)):
    """
    データベース接続情報とテーブル存在確認
    """
    try:
        # データベース接続テスト
        result = db.execute("SELECT 1 as test").fetchone()
        
        # usersテーブルの存在確認とレコード数取得
        user_count = db.query(User).count()
        
        # データベースの種類を確認
        from models import SQLALCHEMY_DATABASE_URL
        db_type = "MySQL" if SQLALCHEMY_DATABASE_URL.startswith("mysql") else "SQLite"
        
        return {
            "status": "success",
            "database_type": db_type,
            "connection_test": "OK" if result else "Failed",
            "users_table_exists": True,
            "total_users": user_count,
            "database_url": SQLALCHEMY_DATABASE_URL.split('@')[0] + "@***" if '@' in SQLALCHEMY_DATABASE_URL else "Local SQLite"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database info error: {str(e)}")

@router.delete("/cleanup-test-users")
def cleanup_test_users(db: Session = Depends(get_db)):
    """
    テスト用ユーザー（メールアドレスに'test-user-'を含むもの）を削除
    """
    try:
        test_users = db.query(User).filter(User.email.like("%test-user-%")).all()
        deleted_count = len(test_users)
        
        for user in test_users:
            db.delete(user)
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Deleted {deleted_count} test users",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")