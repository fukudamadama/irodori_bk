"""
レシピサービス
レシピテンプレートのコピーやユーザーレシピの管理機能を提供
"""
from typing import List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from models import (
    RecipeTemplate as RecipeTemplateModel, 
    RuleTemplate as RuleTemplateModel,
    Recipe as RecipeModel,
    Rule as RuleModel,
    User,
    RecipeRule
)
from schemas import (
    RecipeWithUserAndRulesWithTriggerAndAction,
    RuleWithTriggerAndAction,
    UserResponse,
    Trigger,
    Action
)
from .user_validation_service import UserValidationService


class RecipeService:
    """レシピに関するビジネスロジックを管理するサービスクラス"""
    
    @staticmethod
    def create_recipe(
        recipe_template_id: int, 
        user_id: int, 
        db_session: Session
    ) -> RecipeWithUserAndRulesWithTriggerAndAction:
        """
        レシピテンプレートをコピーして、ユーザーのレシピとして保存
        
        Args:
            recipe_template_id: レシピテンプレートID
            user_id: ユーザーID
            db_session: データベースセッション
            
        Returns:
            RecipeWithUserAndRulesWithTriggerAndAction: 作成されたレシピ
            
        Raises:
            ValueError: レシピテンプレートまたはユーザーが存在しない場合
            RuntimeError: レシピの作成に失敗した場合
        """
        try:
            # ユーザー存在確認
            UserValidationService.validate_user_exists(user_id, db_session)
            
            # レシピテンプレートの存在確認と取得
            recipe_template = RecipeService._get_recipe_template_with_relations(
                recipe_template_id, db_session
            )
            
            if not recipe_template:
                raise ValueError(f"レシピテンプレートID {recipe_template_id} が見つかりません")
            
            # レシピインスタンスを作成
            recipe_instance = RecipeModel(
                name=recipe_template.name,
                description=recipe_template.description,
                template_id=recipe_template.id,
                user_id=user_id
            )
            db_session.add(recipe_instance)
            db_session.flush()  # IDを取得するためにflush
            
            # 関連するルールテンプレートをルールインスタンスとしてコピー
            rule_instances = []
            for rule_template in recipe_template.rule_templates:
                rule_instance = RuleModel(
                    user_id=user_id,
                    name=rule_template.name,
                    description=rule_template.description,
                    category=rule_template.category,
                    template_id=rule_template.id,
                    trigger_id=rule_template.trigger_id,
                    trigger_params=rule_template.trigger_params,
                    action_id=rule_template.action_id,
                    action_params=rule_template.action_params
                )
                db_session.add(rule_instance)
                rule_instances.append(rule_instance)
            
            db_session.flush()  # ルールのIDを取得するためにflush
            
            # レシピとルールの関連付け
            for rule_instance in rule_instances:
                recipe_rule = RecipeRule(
                    recipe_id=recipe_instance.id,
                    rule_id=rule_instance.id
                )
                db_session.add(recipe_rule)
            
            # レシピテンプレートのコピー数を増加
            recipe_template.copies_count += 1
            
            db_session.commit()
            
            # 作成されたレシピの詳細情報を取得してレスポンス用に変換
            created_recipe = RecipeService._get_recipe_with_relations(
                recipe_instance.id, db_session
            )
            
            return RecipeService._convert_recipe_to_response(created_recipe)
            
        except ValueError:
            db_session.rollback()
            raise
        except Exception as e:
            db_session.rollback()
            raise RuntimeError(f"レシピの作成に失敗しました: {str(e)}")
    
    @staticmethod
    def get_recipes(
        user_id: int, 
        db_session: Session
    ) -> List[RecipeWithUserAndRulesWithTriggerAndAction]:
        """
        ユーザーが利用中のレシピのリストを取得
        
        Args:
            user_id: ユーザーID
            db_session: データベースセッション
            
        Returns:
            List[RecipeWithUserAndRulesWithTriggerAndAction]: ユーザーのレシピリスト
            
        Raises:
            ValueError: ユーザーが存在しない場合
            RuntimeError: レシピの取得に失敗した場合
        """
        try:
            # ユーザー存在確認
            UserValidationService.validate_user_exists(user_id, db_session)
            
            # ユーザーのレシピを取得
            user_recipes = db_session.query(RecipeModel).filter(
                RecipeModel.user_id == user_id
            ).options(
                joinedload(RecipeModel.user),
                joinedload(RecipeModel.template),
                joinedload(RecipeModel.rules).joinedload(RuleModel.trigger),
                joinedload(RecipeModel.rules).joinedload(RuleModel.action)
            ).all()
            
            # レスポンス形式に変換
            return [
                RecipeService._convert_recipe_to_response(recipe)
                for recipe in user_recipes
            ]
            
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"レシピの取得に失敗しました: {str(e)}")
    
    @staticmethod
    def _get_recipe_template_with_relations(
        recipe_template_id: int, 
        db_session: Session
    ) -> RecipeTemplateModel:
        """関連データを含むレシピテンプレートを取得"""
        return db_session.query(RecipeTemplateModel).filter(
            RecipeTemplateModel.id == recipe_template_id
        ).options(
            joinedload(RecipeTemplateModel.author),
            joinedload(RecipeTemplateModel.rule_templates).joinedload(RuleTemplateModel.trigger),
            joinedload(RecipeTemplateModel.rule_templates).joinedload(RuleTemplateModel.action)
        ).first()
    
    @staticmethod
    def _get_recipe_with_relations(recipe_id: int, db_session: Session) -> RecipeModel:
        """関連データを含むレシピを取得"""
        return db_session.query(RecipeModel).filter(
            RecipeModel.id == recipe_id
        ).options(
            joinedload(RecipeModel.user),
            joinedload(RecipeModel.template),
            joinedload(RecipeModel.rules).joinedload(RuleModel.trigger),
            joinedload(RecipeModel.rules).joinedload(RuleModel.action)
        ).first()
    
    @staticmethod
    def _convert_recipe_to_response(
        recipe: RecipeModel
    ) -> RecipeWithUserAndRulesWithTriggerAndAction:
        """レシピインスタンスをレスポンス形式に変換"""
        
        # ルールインスタンスをレスポンス形式に変換
        rules = [
            RuleWithTriggerAndAction(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                category=rule.category,
                created_at=rule.created_at,
                updated_at=rule.updated_at,
                trigger=Trigger.model_validate(rule.trigger),
                trigger_params=rule.trigger_params,
                action=Action.model_validate(rule.action),
                action_params=rule.action_params
            )
            for rule in recipe.rules
        ]
        
        return RecipeWithUserAndRulesWithTriggerAndAction(
            id=recipe.id,
            name=recipe.name,
            description=recipe.description,
            created_at=recipe.created_at,
            updated_at=recipe.updated_at,
            user=UserResponse.model_validate(recipe.user),
            rules=rules
        )