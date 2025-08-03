"""
サービスファクトリー - 依存性注入とサービス管理
"""
from typing import Optional
from .openai_service import OpenAIService, OpenAIServiceConfig
from .financial_service import FinancialService
from .recipe_recommendation_service import RecipeRecommendationService
from .preference_service import PreferenceService


class ServiceFactory:
    """サービスのファクトリークラス"""
    
    @staticmethod
    def create_openai_service(api_key: Optional[str] = None) -> OpenAIService:
        """
        OpenAIサービスを作成
        
        Args:
            api_key: APIキー（指定されない場合は環境変数から取得）
            
        Returns:
            OpenAIService: OpenAIサービスのインスタンス
        """
        return OpenAIService(api_key=api_key)
    
    @staticmethod
    def is_openai_configured() -> bool:
        """
        OpenAIが正しく設定されているかチェック
        
        Returns:
            bool: 設定されている場合True
        """
        return OpenAIServiceConfig.is_api_key_configured()
    
    @staticmethod
    def create_financial_service() -> FinancialService:
        """
        財務サービスを作成
        
        Returns:
            FinancialService: 財務サービスのインスタンス
        """
        return FinancialService()
    
    @staticmethod
    def create_recipe_recommendation_service() -> RecipeRecommendationService:
        """
        レシピ推奨サービスを作成
        
        Returns:
            RecipeRecommendationService: レシピ推奨サービスのインスタンス
        """
        financial_service = ServiceFactory.create_financial_service()
        openai_service = ServiceFactory.create_openai_service()
        return RecipeRecommendationService(
            financial_service=financial_service,
            openai_service=openai_service
        )
    
    @staticmethod
    def create_preference_service() -> PreferenceService:
        """
        ユーザー設定サービスを作成
        
        Returns:
            PreferenceService: ユーザー設定サービスのインスタンス
        """
        return PreferenceService()


