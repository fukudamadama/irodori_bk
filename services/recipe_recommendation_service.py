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
        self.financial_service = financial_service
        self.openai_service = openai_service
    
    def get_recommended_recipes_for_user(
        self, 
        user_id: int, 
        db: Session
    ) -> List[RecipeTemplateWithUserAndRuleTemplatesWithTriggerAndAction]:
        """
        指定されたユーザーに推奨されるレシピテンプレートを取得
        
        Args:
            user_id: ユーザーID
            db: データベースセッション
            
        Returns:
            List[RecipeTemplateWithUserAndRuleTemplatesWithTriggerAndAction]: 推奨レシピのリスト
            
        Raises:
            ValueError: ユーザーが存在しない場合
            RuntimeError: データ取得に失敗した場合
        """
        # ユーザー存在確認
        self._validate_user_exists(user_id, db)
        
        # 財務データを取得
        financial_data = self._get_financial_data(user_id, db)
        
        # 推奨レシピIDを取得
        recommended_recipe_ids = self._get_recommended_recipe_ids(financial_data, db)
        
        # 詳細なレシピテンプレートを取得
        recipe_templates = self._fetch_recipe_templates_with_relations(
            recommended_recipe_ids, db
        )
        
        # レスポンススキーマに変換
        return self._convert_to_response_schema(recipe_templates)
    
    def _validate_user_exists(self, user_id: int, db: Session) -> None:
        """ユーザーの存在を確認"""
        UserValidationService.validate_user_exists(user_id, db)
    
    def _get_financial_data(self, user_id: int, db: Session) -> dict:
        """財務データを取得"""
        if not self.financial_service:
            raise RuntimeError("財務サービスが設定されていません")
        try:
            return self.financial_service.generate_financial_report_data(user_id, db)
        except Exception as e:
            raise RuntimeError(f"財務データの取得に失敗しました: {str(e)}")
    
    def _get_recommended_recipe_ids(self, financial_data: dict, db: Session) -> List[int]:
        """OpenAIサービスを使用して推奨レシピIDを取得"""
        if not self.openai_service:
            raise RuntimeError("OpenAIサービスが設定されていません")
        try:
            # 全ての公開レシピテンプレートを取得
            all_recipe_templates = db.query(RecipeTemplateModel).filter(
                RecipeTemplateModel.is_public == True
            ).all()
            
            # OpenAIサービスを使用してユーザーに適したレシピテンプレートを絞り込む
            return self.openai_service.generate_recommended_recipe_templates(
                financial_data["user_preferences"], 
                financial_data["transactions"],
                all_recipe_templates
            )
        except Exception as e:
            raise RuntimeError(f"レシピ推奨の生成に失敗しました: {str(e)}")
    
    def _fetch_recipe_templates_with_relations(
        self, 
        recipe_ids: List[int], 
        db: Session
    ) -> List[RecipeTemplateModel]:
        """リレーションシップを含むレシピテンプレートを取得"""
        try:
            return db.query(RecipeTemplateModel).options(
                joinedload(RecipeTemplateModel.author),
                joinedload(RecipeTemplateModel.rule_templates).joinedload(RuleTemplateModel.trigger),
                joinedload(RecipeTemplateModel.rule_templates).joinedload(RuleTemplateModel.action)
            ).filter(
                RecipeTemplateModel.id.in_(recipe_ids)
            ).all()
        except Exception as e:
            raise RuntimeError(f"レシピテンプレートの取得に失敗しました: {str(e)}")
    
    def _convert_to_response_schema(
        self, 
        recipe_templates: List[RecipeTemplateModel]
    ) -> List[RecipeTemplateWithUserAndRuleTemplatesWithTriggerAndAction]:
        """レシピテンプレートをレスポンススキーマに変換"""
        results = []
        
        for recipe_template in recipe_templates:
            # ルールテンプレートの変換
            rule_templates_with_triggers_actions = self._convert_rule_templates(
                recipe_template.rule_templates
            )
            
            # レシピテンプレートの変換
            recipe_with_rules = RecipeTemplateWithUserAndRuleTemplatesWithTriggerAndAction(
                id=recipe_template.id,
                name=recipe_template.name,
                description=recipe_template.description,
                author_id=recipe_template.author_id,
                is_public=recipe_template.is_public,
                likes_count=recipe_template.likes_count,
                copies_count=recipe_template.copies_count,
                created_at=recipe_template.created_at,
                updated_at=recipe_template.updated_at,
                user=UserResponse.model_validate(recipe_template.author),
                rules=rule_templates_with_triggers_actions
            )
            results.append(recipe_with_rules)
        
        return results
    
    def _convert_rule_templates(
        self, 
        rule_templates: List[RuleTemplateModel]
    ) -> List[RuleTemplateWithTriggerAndAction]:
        """ルールテンプレートをレスポンススキーマに変換"""
        return [
            RuleTemplateWithTriggerAndAction(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                category=rule.category,
                author_id=rule.author_id,
                is_public=rule.is_public,
                likes_count=rule.likes_count,
                copies_count=rule.copies_count,
                created_at=rule.created_at,
                updated_at=rule.updated_at,
                trigger=Trigger.model_validate(rule.trigger),
                trigger_params=rule.trigger_params,
                action=Action.model_validate(rule.action),
                action_params=rule.action_params
            )
            for rule in rule_templates
        ]