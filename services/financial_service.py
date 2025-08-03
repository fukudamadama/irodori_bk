"""
財務関連のビジネスロジックを担当するサービス
"""

from typing import List, Dict, Any
from collections import defaultdict
from sqlalchemy.orm import Session
from models import Preference as PreferenceModel
from constants import FINANCIAL_PROVIDER_QUESTION, DEMO_FINANCIAL_PROVIDERS
import os


class FinancialService:
    """財務データの処理と分析を担当するサービス"""
    
    def __init__(self):
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    
    def _debug_log(self, message: str) -> None:
        """デバッグメッセージを条件付きで出力"""
        if self.debug_mode:
            print(f"[FinancialService] Debug: {message}")
    
    def get_user_selected_providers(self, user_id: int, db_session: Session) -> List[str]:
        """ユーザーが選択した金融プロバイダーのリストを取得"""
        preference_entities = db_session.query(PreferenceModel).filter(
            PreferenceModel.user_id == user_id,
            PreferenceModel.question == FINANCIAL_PROVIDER_QUESTION
        ).all()
        
        selected_providers = []
        for preference_entity in preference_entities:
            if preference_entity.selected_answers:
                providers = [provider.strip() for provider in preference_entity.selected_answers.split(";") if provider.strip()]
                selected_providers.extend(providers)
        
        self._debug_log(f"ユーザー {user_id} の金融プロバイダーを取得: {selected_providers}")
        return selected_providers
    
    def get_financial_transactions(self, selected_providers: List[str]) -> List[Dict[str, Any]]:
        """選択されたプロバイダーに基づいて金融取引データを取得"""
        financial_transactions = []
        
        for provider_data in DEMO_FINANCIAL_PROVIDERS:
            if provider_data["name"] in selected_providers:
                financial_transactions.extend(provider_data["transactions"])
                self._debug_log(f"{provider_data['name']} からの取引データを追加")
        
        # フォールバック: マッチするプロバイダーがない場合はすべてのデモデータを使用
        if not financial_transactions:
            self._debug_log("マッチするプロバイダーが見つからないため、全てのデモデータを使用")
            for provider_data in DEMO_FINANCIAL_PROVIDERS:
                financial_transactions.extend(provider_data["transactions"])
        
        self._debug_log(f"取得した取引データの総数: {len(financial_transactions)}")
        return financial_transactions
    
    def calculate_expenses_by_category(self, financial_transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """取引データからカテゴリ別支出を計算"""
        category_totals = defaultdict(int)
        
        for transaction_data in financial_transactions:
            category = transaction_data.get("category")
            amount = transaction_data.get("amount", 0)
            if category:
                category_totals[category] += amount
        
        expenses_by_category = [
            {"category": category, "total_amount": total_amount}
            for category, total_amount in category_totals.items()
        ]
        
        self._debug_log(f"{len(expenses_by_category)} カテゴリの支出を計算")
        return expenses_by_category
    
    def generate_financial_report_data(self, user_id: int, db_session: Session) -> Dict[str, Any]:
        """財務レポート用のデータを生成"""
        # 0. ユーザー存在確認
        from .user_validation_service import UserValidationService
        UserValidationService.validate_user_exists(user_id, db_session)
        
        # 1. ユーザーが選択した金融プロバイダーを取得
        selected_providers = self.get_user_selected_providers(user_id, db_session)
        
        # 2. 選択されたプロバイダーの取引データを取得
        financial_transactions = self.get_financial_transactions(selected_providers)
        
        # 3. カテゴリ別支出を計算
        expenses_by_category = self.calculate_expenses_by_category(financial_transactions)
        
        # 4. ユーザーの設定を取得（OpenAI分析用）
        user_preference_entities = db_session.query(PreferenceModel).filter(
            PreferenceModel.user_id == user_id
        ).all()
        
        return {
            "selected_providers": selected_providers,
            "transactions": financial_transactions,
            "expenses_by_category": expenses_by_category,
            "user_preferences": user_preference_entities
        }