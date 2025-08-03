"""
ユーザー設定（Preference）関連のビジネスロジックを担当するサービス
"""

from typing import List
from sqlalchemy.orm import Session
from models import Preference as PreferenceModel, User
from schemas import PreferenceCreate, Preference
from .user_validation_service import UserValidationService


class PreferenceService:
    """ユーザー設定の作成・取得・変換を担当するサービスクラス"""
    
    @staticmethod
    def create_single_preference(preference_data: PreferenceCreate, db_session: Session) -> Preference:
        """
        単一のユーザー設定を作成
        
        Args:
            preference_data: 作成する設定データ
            db_session: データベースセッション
            
        Returns:
            Preference: 作成された設定のレスポンス形式
            
        Raises:
            ValueError: ユーザーが存在しない場合
        """
        # ユーザー存在確認
        UserValidationService.validate_user_exists(preference_data.user_id, db_session)
        
        # 回答をセミコロン区切りの文字列に変換
        answers_as_string = ";".join(preference_data.selected_answers)
        
        # データベースエンティティを作成
        preference_entity = PreferenceModel(
            user_id=preference_data.user_id,
            question=preference_data.question,
            selected_answers=answers_as_string
        )
        
        # データベースに保存
        db_session.add(preference_entity)
        db_session.commit()
        db_session.refresh(preference_entity)
        
        # レスポンス形式に変換して返す
        return PreferenceConverter.entity_to_schema(preference_entity)
    
    @staticmethod
    def create_multiple_preferences(preferences_data: List[PreferenceCreate], db_session: Session) -> List[Preference]:
        """
        複数のユーザー設定を一括作成
        
        Args:
            preferences_data: 作成する設定データのリスト
            db_session: データベースセッション
            
        Returns:
            List[Preference]: 作成された設定のレスポンス形式リスト
            
        Raises:
            ValueError: ユーザーが存在しない場合
            RuntimeError: データベース操作に失敗した場合
        """
        created_preference_entities = []
        
        try:
            # 複数の設定を一括処理
            for preference_data in preferences_data:
                # ユーザー存在確認
                UserValidationService.validate_user_exists(preference_data.user_id, db_session)
                
                # 回答をセミコロン区切りの文字列に変換
                answers_as_string = ";".join(preference_data.selected_answers)
                
                # データベースエンティティを作成
                preference_entity = PreferenceModel(
                    user_id=preference_data.user_id,
                    question=preference_data.question,
                    selected_answers=answers_as_string
                )
                
                db_session.add(preference_entity)
                created_preference_entities.append(preference_entity)
            
            # 一括でコミット
            db_session.commit()
            
            # 作成されたエンティティをレスポンス形式に変換
            response_preferences = []
            for preference_entity in created_preference_entities:
                db_session.refresh(preference_entity)
                response_preferences.append(
                    PreferenceConverter.entity_to_schema(preference_entity)
                )
            
            return response_preferences
            
        except ValueError:
            # ユーザー存在確認でのエラーはそのまま再発生
            db_session.rollback()
            raise
        except Exception as e:
            # その他のエラーはランタイムエラーとして処理
            db_session.rollback()
            raise RuntimeError(f"設定の保存に失敗しました: {str(e)}")
    
    @staticmethod
    def get_user_preferences(user_id: int, db_session: Session) -> List[Preference]:
        """
        指定されたユーザーの設定を取得
        
        Args:
            user_id: ユーザーID
            db_session: データベースセッション
            
        Returns:
            List[Preference]: ユーザーの設定リスト
        """
        # 指定されたユーザーIDの設定を取得
        preference_entities = db_session.query(PreferenceModel).filter(
            PreferenceModel.user_id == user_id
        ).all()
        
        # レスポンス形式に変換
        return [
            PreferenceConverter.entity_to_schema(preference_entity)
            for preference_entity in preference_entities
        ]


class PreferenceConverter:
    """Preferenceエンティティとスキーマ間の変換を担当するクラス"""
    
    @staticmethod
    def entity_to_schema(preference_entity: PreferenceModel) -> Preference:
        """
        PreferenceモデルをPreferenceスキーマに変換
        
        Args:
            preference_entity: データベースのPreferenceエンティティ
            
        Returns:
            Preference: レスポンス用のスキーマ
        """
        # セミコロン区切りの文字列を配列に変換
        selected_answers = (
            preference_entity.selected_answers.split(";") 
            if preference_entity.selected_answers else []
        )
        
        return Preference(
            id=preference_entity.id,
            user_id=preference_entity.user_id,
            question=preference_entity.question,
            selected_answers=selected_answers
        )