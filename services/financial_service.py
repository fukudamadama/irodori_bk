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
        """ユーザーが選択した金融プロバイダーのリストを取得
        現行仕様（連携カード/連携銀行）と旧仕様（FINANCIAL_PROVIDER_QUESTION）の両方に対応
        """
        accepted_questions = [
            FINANCIAL_PROVIDER_QUESTION,
            "連携カード",
            "連携銀行",
        ]
        preference_entities = db_session.query(PreferenceModel).filter(
            PreferenceModel.user_id == user_id,
            PreferenceModel.question.in_(accepted_questions)
        ).all()
        
        selected_providers = []
        for preference_entity in preference_entities:
            if preference_entity.selected_answers:
                providers = [provider.strip() for provider in preference_entity.selected_answers.split(";") if provider.strip()]
                selected_providers.extend(providers)
        
        self._debug_log(f"ユーザー {user_id} の金融プロバイダーを取得: {selected_providers}")
        return selected_providers
    
    def get_financial_transactions(self, selected_providers: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """選択されたプロバイダーに基づいて金融取引データを取得（銀行/カードを分離）"""
        income_transactions: List[Dict[str, Any]] = []
        expense_transactions: List[Dict[str, Any]] = []
        
        for provider_data in DEMO_FINANCIAL_PROVIDERS:
            if provider_data["name"] in selected_providers:
                # 名前により銀行/カードを判定
                is_bank = "銀行" in provider_data["name"]
                is_card = "カード" in provider_data["name"]
                if is_bank:
                    income_transactions.extend(provider_data["transactions"])  # 正の金額が収入
                elif is_card:
                    expense_transactions.extend(provider_data["transactions"])  # 負の金額が支出
                self._debug_log(f"{provider_data['name']} からの取引データを追加")
        
        # フォールバック: 何も選択されなかった場合のみ全デモデータ
        if not income_transactions and not expense_transactions:
            self._debug_log("マッチするプロバイダーが見つからないため、全てのデモデータを使用")
            for provider_data in DEMO_FINANCIAL_PROVIDERS:
                if "銀行" in provider_data["name"]:
                    income_transactions.extend(provider_data["transactions"]) 
                if "カード" in provider_data["name"]:
                    expense_transactions.extend(provider_data["transactions"]) 
        
        self._debug_log(
            f"取得した取引データ: income={len(income_transactions)}件, expense={len(expense_transactions)}件"
        )
        return {"income": income_transactions, "expense": expense_transactions}
    
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
        tx = self.get_financial_transactions(selected_providers)
        
        # 3. カテゴリ別支出を計算（カード支出のみ）
        expenses_by_category = self.calculate_expenses_by_category(tx["expense"])
        
        # 4. ユーザーの設定を取得（OpenAI分析用）
        user_preference_entities = db_session.query(PreferenceModel).filter(
            PreferenceModel.user_id == user_id
        ).all()
        
        return {
            "selected_providers": selected_providers,
            "transactions": {"income": tx["income"], "expense": tx["expense"]},
            "expenses_by_category": expenses_by_category,
            "user_preferences": user_preference_entities
        }