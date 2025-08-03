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
    
    def _format_user_preferences(self, preferences) -> str:
        """
        ユーザーの設定をフォーマット
        
        Args:
            preferences: PreferenceModelのクエリ結果
            
        Returns:
            str: フォーマットされたユーザー回答
        """
        user_preferences = ""
        for pref in preferences:
            user_preferences += f"質問: {pref.question}\n回答: {pref.selected_answers}\n\n"
        return user_preferences
    
    def _format_transaction_summary(self, transactions: List[dict]) -> str:
        """
        トランザクションサマリーをフォーマット
        
        Args:
            transactions: トランザクションデータのリスト
            
        Returns:
            str: フォーマットされたトランザクション概要
        """
        transaction_summary = ""
        for tx in transactions:
            transaction_summary += f"カテゴリ: {tx['category']}, 金額: {tx['amount']}円\n"
        return transaction_summary
    
    def generate_financial_insights(self, preferences, transactions: List[dict]) -> List[str]:
        """
        財務インサイトを生成
        
        Args:
            preferences: ユーザーの設定データ
            transactions: トランザクションデータのリスト
            
        Returns:
            List[str]: 生成されたインサイトのリスト
        """
        # APIキーが設定されていない場合はフォールバックを返す
        if not self.client:
            print("OpenAI APIキーが設定されていません。フォールバックインサイトを返します。")
            return FinancialAnalysisPrompts.get_fallback_insights()
        
        try:
            # データをフォーマット
            user_preferences = self._format_user_preferences(preferences)
            transaction_summary = self._format_transaction_summary(transactions)
            
            # プロンプトを生成
            prompt = FinancialAnalysisPrompts.get_financial_insight_prompt(
                user_preferences, transaction_summary
            )
            
            # OpenAI APIを呼び出し
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            # レスポンスからinsightsを抽出
            response_text = response.choices[0].message.content
            
            try:
                parsed_response = json.loads(response_text)
                insights = parsed_response.get("insights", [])
                
                if not insights:  # insightsが空の場合
                    return FinancialAnalysisPrompts.get_json_parse_error_insights()
                    
                return insights
                
            except json.JSONDecodeError as e:
                print(f"JSONパースエラー: {e}")
                return FinancialAnalysisPrompts.get_json_parse_error_insights()
                
        except Exception as e:
            print(f"OpenAI API呼び出しエラー: {e}")
            return FinancialAnalysisPrompts.get_fallback_insights()
    
    def _format_available_recipes(self, recipe_templates) -> str:
        """
        利用可能なレシピテンプレートをフォーマット
        
        Args:
            recipe_templates: RecipeTemplateModelのクエリ結果
            
        Returns:
            str: フォーマットされたレシピテンプレート一覧
        """
        available_recipes = ""
        for recipe in recipe_templates:
            available_recipes += f"ID: {recipe.id}, 名前: {recipe.name}, 説明: {recipe.description}\n"
        return available_recipes
    
    def generate_recommended_recipe_templates(self, preferences, transactions: List[dict], recipe_templates) -> List[int]:
        """
        推奨レシピテンプレートIDを生成
        
        Args:
            preferences: ユーザーの設定データ
            transactions: トランザクションデータのリスト
            recipe_templates: 利用可能なレシピテンプレート一覧
            
        Returns:
            List[int]: 推奨されたレシピテンプレートIDのリスト（最大3件）
        """
        # APIキーが設定されていない場合はフォールバックを返す
        if not self.client:
            print("OpenAI APIキーが設定されていません。フォールバックレシピを返します。")
            return FinancialAnalysisPrompts.get_fallback_recipe_recommendations()
        
        try:
            # データをフォーマット
            user_preferences = self._format_user_preferences(preferences)
            transaction_summary = self._format_transaction_summary(transactions)
            available_recipes = self._format_available_recipes(recipe_templates)
            
            # プロンプトを生成
            prompt = FinancialAnalysisPrompts.get_recipe_recommendation_prompt(
                user_preferences, transaction_summary, available_recipes
            )
            
            # OpenAI APIを呼び出し
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            # レスポンスからレシピIDを抽出
            response_text = response.choices[0].message.content
            
            try:
                parsed_response = json.loads(response_text)
                recommended_ids = parsed_response.get("recommended_recipe_ids", [])
                
                if not recommended_ids:  # IDが空の場合
                    return FinancialAnalysisPrompts.get_json_parse_error_recipe_recommendations()
                
                # 最大3件に制限
                return recommended_ids[:3]
                
            except json.JSONDecodeError as e:
                print(f"JSONパースエラー: {e}")
                return FinancialAnalysisPrompts.get_json_parse_error_recipe_recommendations()
                
        except Exception as e:
            print(f"OpenAI API呼び出しエラー: {e}")
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