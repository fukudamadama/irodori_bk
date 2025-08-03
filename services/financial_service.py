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
    
    def get_user_selected_providers(self, user_id: int, db: Session) -> List[str]:
        """ユーザーが選択した金融プロバイダーのリストを取得"""
        prefs = db.query(PreferenceModel).filter(
            PreferenceModel.user_id == user_id,
            PreferenceModel.question == FINANCIAL_PROVIDER_QUESTION
        ).all()
        
        selected_providers = []
        for pref in prefs:
            if pref.selected_answers:
                providers = [s.strip() for s in pref.selected_answers.split(";") if s.strip()]
                selected_providers.extend(providers)
        
        self._debug_log(f"Retrieved providers for user {user_id}: {selected_providers}")
        return selected_providers
    
    def get_financial_transactions(self, selected_providers: List[str]) -> List[Dict[str, Any]]:
        """選択されたプロバイダーに基づいて金融取引データを取得"""
        transactions = []
        
        for provider in DEMO_FINANCIAL_PROVIDERS:
            if provider["name"] in selected_providers:
                transactions.extend(provider["transactions"])
                self._debug_log(f"Added transactions from {provider['name']}")
        
        # フォールバック: マッチするプロバイダーがない場合はすべてのデモデータを使用
        if not transactions:
            self._debug_log("No matching providers found, using all demo data")
            for provider in DEMO_FINANCIAL_PROVIDERS:
                transactions.extend(provider["transactions"])
        
        self._debug_log(f"Total transactions retrieved: {len(transactions)}")
        return transactions
    
    def calculate_expenses_by_category(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """取引データからカテゴリ別支出を計算"""
        category_totals = defaultdict(int)
        
        for transaction in transactions:
            category = transaction.get("category")
            amount = transaction.get("amount", 0)
            if category:
                category_totals[category] += amount
        
        expenses = [
            {"category": category, "total_amount": total}
            for category, total in category_totals.items()
        ]
        
        self._debug_log(f"Calculated expenses for {len(expenses)} categories")
        return expenses
    
    def generate_financial_report_data(self, user_id: int, db: Session) -> Dict[str, Any]:
        """財務レポート用のデータを生成"""
        # 1. ユーザーが選択した金融プロバイダーを取得
        selected_providers = self.get_user_selected_providers(user_id, db)
        
        # 2. 選択されたプロバイダーの取引データを取得
        transactions = self.get_financial_transactions(selected_providers)
        
        # 3. カテゴリ別支出を計算
        expenses_by_category = self.calculate_expenses_by_category(transactions)
        
        # 4. ユーザーの設定を取得（OpenAI分析用）
        user_preferences = db.query(PreferenceModel).filter(
            PreferenceModel.user_id == user_id
        ).all()
        
        return {
            "selected_providers": selected_providers,
            "transactions": transactions,
            "expenses_by_category": expenses_by_category,
            "user_preferences": user_preferences
        }