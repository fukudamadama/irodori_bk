"""
サービスファクトリー - 依存性注入とサービス管理
"""
from typing import Optional
from .openai_service import OpenAIService, OpenAIServiceConfig
from .financial_service import FinancialService
from .recipe_recommendation_service import RecipeRecommendationService


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


# シングルトンパターンでサービスを管理する場合
class ServiceManager:
    """サービスマネージャー - シングルトンパターン"""
    
    _openai_service: Optional[OpenAIService] = None
    _financial_service: Optional[FinancialService] = None
    _recipe_recommendation_service: Optional[RecipeRecommendationService] = None
    
    @classmethod
    def get_openai_service(cls) -> OpenAIService:
        """
        OpenAIサービスのシングルトンインスタンスを取得
        
        Returns:
            OpenAIService: OpenAIサービスのインスタンス
        """
        if cls._openai_service is None:
            cls._openai_service = OpenAIService()
        return cls._openai_service
    
    @classmethod
    def get_financial_service(cls) -> FinancialService:
        """
        財務サービスのシングルトンインスタンスを取得
        
        Returns:
            FinancialService: 財務サービスのインスタンス
        """
        if cls._financial_service is None:
            cls._financial_service = FinancialService()
        return cls._financial_service
    
    @classmethod
    def get_recipe_recommendation_service(cls) -> RecipeRecommendationService:
        """
        レシピ推奨サービスのシングルトンインスタンスを取得
        
        Returns:
            RecipeRecommendationService: レシピ推奨サービスのインスタンス
        """
        if cls._recipe_recommendation_service is None:
            financial_service = cls.get_financial_service()
            openai_service = cls.get_openai_service()
            cls._recipe_recommendation_service = RecipeRecommendationService(
                financial_service=financial_service,
                openai_service=openai_service
            )
        return cls._recipe_recommendation_service
    
    @classmethod
    def reset_services(cls):
        """サービスインスタンスをリセット（テスト用）"""
        cls._openai_service = None
        cls._financial_service = None
        cls._recipe_recommendation_service = None