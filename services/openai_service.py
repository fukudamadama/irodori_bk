"""
OpenAI API サービス
"""
import os
import json
import openai
from typing import List, Optional
from .prompt_templates import FinancialAnalysisPrompts


class OpenAIService:
    """OpenAI API呼び出しを管理するサービスクラス"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        OpenAIサービスを初期化
        
        Args:
            api_key: OpenAI APIキー。指定されない場合は環境変数から取得
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
    
    def _format_user_preferences(self, preference_entities) -> str:
        """
        ユーザーの設定をフォーマット
        
        Args:
            preference_entities: PreferenceModelのクエリ結果
            
        Returns:
            str: フォーマットされたユーザー回答
        """
        formatted_preferences = ""
        for preference_entity in preference_entities:
            formatted_preferences += f"質問: {preference_entity.question}\n回答: {preference_entity.selected_answers}\n\n"
        return formatted_preferences
    
    def _format_transaction_summary(self, financial_transactions: List[dict]) -> str:
        """
        取引データの概要をフォーマット
        
        Args:
            financial_transactions: 取引データのリスト
            
        Returns:
            str: フォーマットされた取引データ概要
        """
        formatted_transaction_summary = ""
        for transaction_data in financial_transactions:
            formatted_transaction_summary += f"カテゴリ: {transaction_data['category']}, 金額: {transaction_data['amount']}円\n"
        return formatted_transaction_summary
    
    def generate_financial_insights(self, preference_entities, financial_transactions: List[dict]) -> List[str]:
        """
        財務インサイトを生成
        
        Args:
            preference_entities: ユーザーの設定データ
            financial_transactions: 取引データのリスト
            
        Returns:
            List[str]: 生成されたインサイトのリスト
        """
        # APIキーが設定されていない場合はフォールバックを返す
        if not self.client:
            print("OpenAI APIキーが設定されていません。フォールバックインサイトを返します。")
            return FinancialAnalysisPrompts.get_fallback_insights()
        
        try:
            # データをフォーマット
            formatted_user_preferences = self._format_user_preferences(preference_entities)
            formatted_transaction_summary = self._format_transaction_summary(financial_transactions)
            
            # プロンプトを生成
            analysis_prompt = FinancialAnalysisPrompts.get_financial_insight_prompt(
                formatted_user_preferences, formatted_transaction_summary
            )
            
            # OpenAI APIを呼び出し
            api_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            # レスポンスからinsightsを抽出
            response_content = api_response.choices[0].message.content
            
            try:
                parsed_json_response = json.loads(response_content)
                generated_insights = parsed_json_response.get("insights", [])
                
                if not generated_insights:  # insightsが空の場合
                    return FinancialAnalysisPrompts.get_json_parse_error_insights()
                    
                return generated_insights
                
            except json.JSONDecodeError as json_error:
                print(f"JSONパースエラー: {json_error}")
                return FinancialAnalysisPrompts.get_json_parse_error_insights()
                
        except Exception as api_error:
            print(f"OpenAI API呼び出しエラー: {api_error}")
            return FinancialAnalysisPrompts.get_fallback_insights()
    
    def _format_available_recipes(self, recipe_template_entities) -> str:
        """
        利用可能なレシピテンプレートをフォーマット
        
        Args:
            recipe_template_entities: RecipeTemplateModelのクエリ結果
            
        Returns:
            str: フォーマットされたレシピテンプレート一覧
        """
        formatted_available_recipes = ""
        for recipe_template_entity in recipe_template_entities:
            formatted_available_recipes += f"ID: {recipe_template_entity.id}, 名前: {recipe_template_entity.name}, 説明: {recipe_template_entity.description}\n"
        return formatted_available_recipes
    
    def generate_recommended_recipe_templates(self, preference_entities, financial_transactions: List[dict], recipe_template_entities) -> List[int]:
        """
        推奨レシピテンプレートIDを生成
        
        Args:
            preference_entities: ユーザーの設定データ
            financial_transactions: 取引データのリスト
            recipe_template_entities: 利用可能なレシピテンプレート一覧
            
        Returns:
            List[int]: 推奨されたレシピテンプレートIDのリスト（最大3件）
        """
        # APIキーが設定されていない場合はフォールバックを返す
        if not self.client:
            print("OpenAI APIキーが設定されていません。フォールバックレシピを返します。")
            return FinancialAnalysisPrompts.get_fallback_recipe_recommendations()
        
        try:
            # データをフォーマット
            formatted_user_preferences = self._format_user_preferences(preference_entities)
            formatted_transaction_summary = self._format_transaction_summary(financial_transactions)
            formatted_available_recipes = self._format_available_recipes(recipe_template_entities)
            
            # プロンプトを生成
            recommendation_prompt = FinancialAnalysisPrompts.get_recipe_recommendation_prompt(
                formatted_user_preferences, formatted_transaction_summary, formatted_available_recipes
            )
            
            # OpenAI APIを呼び出し
            api_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": recommendation_prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            # レスポンスからレシピIDを抽出
            response_content = api_response.choices[0].message.content
            
            try:
                parsed_json_response = json.loads(response_content)
                recommended_recipe_ids = parsed_json_response.get("recommended_recipe_ids", [])
                
                if not recommended_recipe_ids:  # IDが空の場合
                    return FinancialAnalysisPrompts.get_json_parse_error_recipe_recommendations()
                
                # 最大3件に制限
                return recommended_recipe_ids[:3]
                
            except json.JSONDecodeError as json_error:
                print(f"JSONパースエラー: {json_error}")
                return FinancialAnalysisPrompts.get_json_parse_error_recipe_recommendations()
                
        except Exception as api_error:
            print(f"OpenAI API呼び出しエラー: {api_error}")
            return FinancialAnalysisPrompts.get_fallback_recipe_recommendations()


class OpenAIServiceConfig:
    """OpenAI サービスの設定クラス"""
    
    DEFAULT_MODEL = "gpt-3.5-turbo"
    DEFAULT_MAX_TOKENS = 500
    DEFAULT_TEMPERATURE = 0.7
    
    @classmethod
    def get_api_key_from_env(cls) -> Optional[str]:
        """環境変数からAPIキーを取得"""
        return os.getenv("OPENAI_API_KEY")
    
    @classmethod
    def is_api_key_configured(cls) -> bool:
        """APIキーが設定されているかチェック"""
        return cls.get_api_key_from_env() is not None