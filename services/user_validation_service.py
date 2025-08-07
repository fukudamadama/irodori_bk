"""
ユーザー検証サービス
"""
from sqlalchemy.orm import Session
from models import User


class UserValidationService:
    """ユーザー検証に関する共通ロジックを管理するサービスクラス"""
    
    @staticmethod
    def validate_user_exists(user_id: int, db: Session) -> User:
        """
        ユーザーの存在を確認し、ユーザーオブジェクトを返す
        
        Args:
            user_id: ユーザーID
            db: データベースセッション
            
        Returns:
            User: ユーザーオブジェクト
            
        Raises:
            ValueError: ユーザーが存在しない場合
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("指定されたユーザーが存在しません")
        return user
    
    @staticmethod
    def user_exists(user_id: int, db: Session) -> bool:
        """
        ユーザーが存在するかどうかをチェック
        
        Args:
            user_id: ユーザーID
            db: データベースセッション
            
        Returns:
            bool: ユーザーが存在する場合True
        """
        return db.query(User).filter(User.id == user_id).first() is not None