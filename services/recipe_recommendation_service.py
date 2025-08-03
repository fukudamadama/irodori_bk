"""
レシピ推奨サービス
"""
from typing import List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from models import RecipeTemplate as RecipeTemplateModel, RuleTemplate as RuleTemplateModel, User
from schemas import (
    RecipeTemplateWithUserAndRuleTemplatesWithTriggerAndAction,
    RuleTemplateWithTriggerAndAction,
    UserResponse,
    Trigger,
    Action
)
from .user_validation_service import UserValidationService


class RecipeRecommendationService:
    """レシピ推奨に関するビジネスロジックを管理するサービスクラス"""
    
    def __init__(self, financial_service=None, openai_service=None):
        """
        レシピ推奨サービスを初期化
        
        Args:
            financial_service: 財務サービスのインスタンス
            openai_service: OpenAIサービスのインスタンス
        """
        self._financial_service = financial_service
        self._openai_service = openai_service
    
    def get_recommended_recipes_for_user(
        self, 
        user_id: int, 
        db_session: Session
    ) -> List[RecipeTemplateWithUserAndRuleTemplatesWithTriggerAndAction]:
        """
        指定されたユーザーに推奨されるレシピテンプレートを取得
        
        Args:
            user_id: ユーザーID
            db_session: データベースセッション
            
        Returns:
            List[RecipeTemplateWithUserAndRuleTemplatesWithTriggerAndAction]: 推奨レシピのリスト
            
        Raises:
            ValueError: ユーザーが存在しない場合
            RuntimeError: データ取得に失敗した場合
        """
        # ユーザー存在確認
        self._validate_user_exists(user_id, db_session)
        
        # 財務データを取得
        user_financial_data = self._get_financial_data(user_id, db_session)
        
        # 推奨レシピIDを取得
        recommended_recipe_ids = self._get_recommended_recipe_ids(user_financial_data, db_session)
        
        # 詳細なレシピテンプレートを取得
        recipe_template_entities = self._fetch_recipe_templates_with_relations(
            recommended_recipe_ids, db_session
        )
        
        # レスポンススキーマに変換
        return self._convert_to_response_schema(recipe_template_entities)
    
    def _validate_user_exists(self, user_id: int, db_session: Session) -> None:
        """ユーザーの存在を確認"""
        UserValidationService.validate_user_exists(user_id, db_session)
    
    def _get_financial_data(self, user_id: int, db_session: Session) -> dict:
        """財務データを取得"""
        if not self._financial_service:
            raise RuntimeError("財務サービスが設定されていません")
        try:
            return self._financial_service.generate_financial_report_data(user_id, db_session)
        except Exception as service_error:
            raise RuntimeError(f"財務データの取得に失敗しました: {str(service_error)}")
    
    def _get_recommended_recipe_ids(self, user_financial_data: dict, db_session: Session) -> List[int]:
        """OpenAIサービスを使用して推奨レシピIDを取得"""
        if not self._openai_service:
            raise RuntimeError("OpenAIサービスが設定されていません")
        try:
            # 全ての公開レシピテンプレートを取得
            public_recipe_template_entities = db_session.query(RecipeTemplateModel).filter(
                RecipeTemplateModel.is_public == True
            ).all()
            
            # OpenAIサービスを使用してユーザーに適したレシピテンプレートを絞り込む
            return self._openai_service.generate_recommended_recipe_templates(
                user_financial_data["user_preferences"], 
                user_financial_data["transactions"],
                public_recipe_template_entities
            )
        except Exception as service_error:
            raise RuntimeError(f"レシピ推奨の生成に失敗しました: {str(service_error)}")
    
    def _fetch_recipe_templates_with_relations(
        self, 
        recommended_recipe_ids: List[int], 
        db_session: Session
    ) -> List[RecipeTemplateModel]:
        """リレーションシップを含むレシピテンプレートを取得"""
        try:
            return db_session.query(RecipeTemplateModel).options(
                joinedload(RecipeTemplateModel.author),
                joinedload(RecipeTemplateModel.rule_templates).joinedload(RuleTemplateModel.trigger),
                joinedload(RecipeTemplateModel.rule_templates).joinedload(RuleTemplateModel.action)
            ).filter(
                RecipeTemplateModel.id.in_(recommended_recipe_ids)
            ).all()
        except Exception as db_error:
            raise RuntimeError(f"レシピテンプレートの取得に失敗しました: {str(db_error)}")
    
    def _convert_to_response_schema(
        self, 
        recipe_template_entities: List[RecipeTemplateModel]
    ) -> List[RecipeTemplateWithUserAndRuleTemplatesWithTriggerAndAction]:
        """レシピテンプレートをレスポンススキーマに変換"""
        response_recipe_templates = []
        
        for recipe_template_entity in recipe_template_entities:
            # ルールテンプレートの変換
            converted_rule_templates = self._convert_rule_templates(
                recipe_template_entity.rule_templates
            )
            
            # レシピテンプレートの変換
            recipe_template_response = RecipeTemplateWithUserAndRuleTemplatesWithTriggerAndAction(
                id=recipe_template_entity.id,
                name=recipe_template_entity.name,
                description=recipe_template_entity.description,
                author_id=recipe_template_entity.author_id,
                is_public=recipe_template_entity.is_public,
                likes_count=recipe_template_entity.likes_count,
                copies_count=recipe_template_entity.copies_count,
                created_at=recipe_template_entity.created_at,
                updated_at=recipe_template_entity.updated_at,
                user=UserResponse.model_validate(recipe_template_entity.author),
                rules=converted_rule_templates
            )
            response_recipe_templates.append(recipe_template_response)
        
        return response_recipe_templates
    
    def _convert_rule_templates(
        self, 
        rule_template_entities: List[RuleTemplateModel]
    ) -> List[RuleTemplateWithTriggerAndAction]:
        """ルールテンプレートをレスポンススキーマに変換"""
        return [
            RuleTemplateWithTriggerAndAction(
                id=rule_template_entity.id,
                name=rule_template_entity.name,
                description=rule_template_entity.description,
                category=rule_template_entity.category,
                author_id=rule_template_entity.author_id,
                is_public=rule_template_entity.is_public,
                likes_count=rule_template_entity.likes_count,
                copies_count=rule_template_entity.copies_count,
                created_at=rule_template_entity.created_at,
                updated_at=rule_template_entity.updated_at,
                trigger=Trigger.model_validate(rule_template_entity.trigger),
                trigger_params=rule_template_entity.trigger_params,
                action=Action.model_validate(rule_template_entity.action),
                action_params=rule_template_entity.action_params
            )
            for rule_template_entity in rule_template_entities
        ]