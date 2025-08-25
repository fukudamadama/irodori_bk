from fastapi import APIRouter, Query, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from schemas import (
    PreferenceCreate, Preference, FinancialReport,
    RecipeWithUserAndRulesWithTriggerAndAction,
    RecipeTemplateWithUserAndRuleTemplatesWithTriggerAndAction,
    RecipeCreate, UserNicknameSet, UserResponse
)
from typing import List
from datetime import datetime
from services.service_factory import ServiceFactory
from services.preference_service import PreferenceService
from services.recipe_service import RecipeService
from services.user_service import UserService
from pydantic import BaseModel
from constants import DEMO_FINANCIAL_PROVIDERS, FINANCIAL_PROVIDER_QUESTION

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

class PreferenceCreateInput(BaseModel):
    question: str
    selected_answers: List[str]

@router.put(
    "/nickname", 
    response_model=UserResponse, 
    status_code=200,
    summary="オンボーディング時にユーザーのニックネームを設定",
)
def set_nickname(nickname_data: UserNicknameSet, db_session: Session = Depends(get_db)):
    """ユーザーのニックネームを設定（ユーザーIDはリクエストBodyで受け取る）"""
    try:
        return UserService.set_nickname(nickname_data, db_session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="ニックネームの設定に失敗しました")

@router.post(
    "/preference", 
    response_model=Preference, 
    status_code=201,
    summary="オンボーディング時にユーザーが回答した、属性・傾向に関する質問と回答を1件保存",
)
def create_preference(preference_data: PreferenceCreateInput, request: Request, user_id: int | None = Query(None, ge=1), db_session: Session = Depends(get_db)):
    """単一のユーザー設定を作成（ユーザーIDはセッションから取得）"""
    try:
        if user_id is None:
            user_id = request.session.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="ログインが必要です")
        model = PreferenceCreate(user_id=user_id, question=preference_data.question, selected_answers=preference_data.selected_answers)
        return PreferenceService.create_single_preference(model, db_session)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="設定の保存に失敗しました")


@router.post(
    "/preferences", 
    response_model=List[Preference], 
    status_code=201,
    summary="オンボーディング時にユーザーが回答した、属性・傾向に関する質問と回答のリストを一括で保存",
)
def create_preferences(preferences_data: List[PreferenceCreateInput], request: Request, user_id: int | None = Query(None, ge=1), db_session: Session = Depends(get_db)):
    """複数のユーザー設定を一括作成（ユーザーIDはセッションから取得）"""
    try:
        if user_id is None:
            user_id = request.session.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="ログインが必要です")
        converted: List[PreferenceCreate] = [
            PreferenceCreate(user_id=user_id, question=item.question, selected_answers=item.selected_answers)
            for item in preferences_data
        ]
        return PreferenceService.create_multiple_preferences(converted, db_session)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="設定の保存に失敗しました")


@router.get(
    "/financial-providers",
    summary="オンボーディングのカード・銀行候補名を取得",
)
def get_financial_providers():
    try:
        card_names = []
        bank_names = []
        for item in DEMO_FINANCIAL_PROVIDERS:
            name = item.get("name", "")
            if "カード" in name:
                card_names.append(name)
            elif "銀行" in name:
                bank_names.append(name)
        # 重複排除
        cards = sorted(list(dict.fromkeys(card_names)))
        banks = sorted(list(dict.fromkeys(bank_names)))
        return {
            "question": FINANCIAL_PROVIDER_QUESTION,
            "cards": cards,
            "banks": banks,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"金融機関連携候補の取得に失敗しました: {str(e)}")

@router.get(
    "/preferences", 
    response_model=List[Preference],
    summary="保存されているユーザーの属性・傾向に関する質問と回答のリストを取得",
)
def get_preferences(user_id: int = Query(..., description="ユーザーID", ge=1), db_session: Session = Depends(get_db)):
    """指定されたユーザーの設定を取得"""
    return PreferenceService.get_user_preferences(user_id, db_session)

@router.get(
    "/financial-report", 
    response_model=FinancialReport,
    summary="ユーザーの財務状況を分析し、インサイトと支出のカテゴリごとの合計金額を取得",
)
def get_financial_report(request: Request, user_id: int | None = Query(None, description="ユーザーID", ge=1), db_session: Session = Depends(get_db)):
    """ユーザーの財務レポートを生成"""
    try:
        # サービスを取得
        financial_service = ServiceFactory.create_financial_service()
        openai_service = ServiceFactory.create_openai_service()
        
        # ユーザーIDが未指定の場合はセッションから取得
        if user_id is None:
            user_id = request.session.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="ログインが必要です")

        # 財務データを取得
        financial_data = financial_service.generate_financial_report_data(int(user_id), db_session)
        
        # OpenAI サービスを使用して財務インサイトを生成
        insights = openai_service.generate_financial_insights(
            financial_data["user_preferences"], 
            financial_data["transactions"]
        )
        
        # 収入/支出総額を算出
        income_total = sum([t.get("amount", 0) for t in financial_data["transactions"]["income"] if t.get("amount", 0) > 0])
        expense_total = sum([abs(t.get("amount", 0)) for t in financial_data["transactions"]["expense"] if t.get("amount", 0) < 0])
        balance_total = income_total - expense_total

        # レポートを構築
        financial_report = {
            "user_id": user_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "insights": insights,
            "expenses_by_category": financial_data["expenses_by_category"],
            "income_total": income_total,
            "expense_total": expense_total,
            "balance_total": balance_total,
            "transactions": financial_data["transactions"],
        }
        
        return financial_report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"財務レポートの生成に失敗しました: {str(e)}")

@router.get(
    "/recommended_recipes", 
    response_model=List[RecipeTemplateWithUserAndRuleTemplatesWithTriggerAndAction],
    summary="ユーザーに対し導入が推奨されるレシピテンプレート(ルールテンプレートを含む)を取得",
)
def get_recommend_recipe_templates(user_id: int = Query(..., description="ユーザーID", ge=1), db_session: Session = Depends(get_db)):
    """ユーザーに推奨されるレシピテンプレートを取得"""
    try:
        # レシピ推奨サービスを取得
        recipe_recommendation_service = ServiceFactory.create_recipe_recommendation_service()
        
        # 推奨レシピを取得
        return recipe_recommendation_service.get_recommended_recipes_for_user(user_id, db_session)
        
    except ValueError as e:
        # ユーザーが存在しない場合
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        # サービス層でのエラー
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # 予期しないエラー
        raise HTTPException(status_code=500, detail=f"推奨レシピの取得に失敗しました: {str(e)}")

@router.post(
    "/recipe", 
    response_model=RecipeWithUserAndRulesWithTriggerAndAction,
    summary="レシピテンプレートをコピーして、ユーザーのレシピテンプレートとして保存",
)
def create_recipe(recipe_data: RecipeCreate, db_session: Session = Depends(get_db)):
    """レシピテンプレートをコピーして、ユーザーのレシピテンプレートとして保存"""
    try:
        return RecipeService.create_recipe(recipe_data.template_id, recipe_data.user_id, db_session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"レシピの作成に失敗しました: {str(e)}")

@router.get(
    "/recipes", 
    response_model=List[RecipeWithUserAndRulesWithTriggerAndAction],
    summary="ユーザーが利用中のレシピのリストを取得",
)
def get_recipes(user_id: int = Query(..., description="ユーザーID", ge=1), db_session: Session = Depends(get_db)):
    """ユーザーが利用中のレシピのリストを取得"""
    try:
        return RecipeService.get_recipes(user_id, db_session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"レシピの取得に失敗しました: {str(e)}")
