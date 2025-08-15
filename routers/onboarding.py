from fastapi import APIRouter, Query, Depends, HTTPException
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

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

@router.put(
    "/nickname", 
    response_model=UserResponse, 
    status_code=200,
    summary="オンボーディング時にユーザーのニックネームを設定",
)
def set_nickname(nickname_data: UserNicknameSet, db_session: Session = Depends(get_db)):
    """ユーザーのニックネームを設定"""
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
def create_preference(preference_data: PreferenceCreate, db_session: Session = Depends(get_db)):
    """単一のユーザー設定を作成"""
    try:
        return PreferenceService.create_single_preference(preference_data, db_session)
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
def create_preferences(preferences_data: List[PreferenceCreate], db_session: Session = Depends(get_db)):
    """複数のユーザー設定を一括作成"""
    try:
        return PreferenceService.create_multiple_preferences(preferences_data, db_session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="設定の保存に失敗しました")

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
def get_financial_report(user_id: int = Query(..., description="ユーザーID", ge=1), db_session: Session = Depends(get_db)):
    """ユーザーの財務レポートを生成"""
    try:
        # サービスを取得
        financial_service = ServiceFactory.create_financial_service()
        openai_service = ServiceFactory.create_openai_service()
        
        # 財務データを取得
        financial_data = financial_service.generate_financial_report_data(user_id, db_session)
        
        # OpenAI サービスを使用して財務インサイトを生成
        insights = openai_service.generate_financial_insights(
            financial_data["user_preferences"], 
            financial_data["transactions"]
        )
        
        # レポートを構築
        financial_report = {
            "user_id": user_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "insights": insights,
            "expenses_by_category": financial_data["expenses_by_category"]
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
