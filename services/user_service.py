"""
ユーザー関連のビジネスロジックを担当するサービス
"""

from sqlalchemy.orm import Session
from models import User
from schemas import UserNicknameSet, UserResponse
from .user_validation_service import UserValidationService


class UserService:
    """ユーザー関連の操作を担当するサービスクラス"""
    
    @staticmethod
    def set_nickname(nickname_data: UserNicknameSet, db_session: Session) -> UserResponse:
        """
        ユーザーのニックネームを設定
        
        Args:
            nickname_data: ニックネーム設定データ
            db_session: データベースセッション
            
        Returns:
            UserResponse: 更新されたユーザー情報
            
        Raises:
            ValueError: ユーザーが存在しない場合やニックネームが既に設定済みの場合
        """
        # ユーザー存在確認
        user = UserValidationService.validate_user_exists(nickname_data.user_id, db_session)
        
        # ニックネームが既に設定されている場合はエラー
        if user.nickname is not None:
            raise ValueError("ニックネームは既に設定済みです")
        
        # ニックネームを設定
        user.nickname = nickname_data.nickname
        
        # データベースに保存
        db_session.commit()
        db_session.refresh(user)
        
        # レスポンス形式に変換して返す
        return UserResponse(
            id=user.id,
            last_name=user.last_name,
            first_name=user.first_name,
            email=user.email,
            birthdate=user.birthdate,
            occupation=user.occupation,
            company_name=user.company_name,
            nickname=user.nickname
        )
    
    @staticmethod
    def get_user(user_id: int, db_session: Session) -> UserResponse:
        """
        ユーザー情報を取得
        
        Args:
            user_id: ユーザーID
            db_session: データベースセッション
            
        Returns:
            UserResponse: ユーザー情報
            
        Raises:
            ValueError: ユーザーが存在しない場合
        """
        user = UserValidationService.validate_user_exists(user_id, db_session)
        
        return UserResponse(
            id=user.id,
            last_name=user.last_name,
            first_name=user.first_name,
            email=user.email,
            birthdate=user.birthdate,
            occupation=user.occupation,
            company_name=user.company_name,
            nickname=user.nickname
        )