from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import (
    Preference as PreferenceModel, User, RecipeTemplate as RecipeTemplateModel, 
    RuleTemplate as RuleTemplateModel, Trigger as TriggerModel, Action as ActionModel,
    RecipeTemplateRuleTemplate
)
from schemas import (
    PreferenceCreate, Preference, 
    RuleTemplateWithTriggerAndAction, Trigger, Action, FinancialReport,
    RecipeTemplateWithUserAndRuleTemplatesWithTriggerAndAction, UserResponse
)
from typing import List
from datetime import datetime
from services.service_factory import ServiceFactory

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

@router.post(
    "/preference", 
    response_model=Preference, 
    status_code=201,
    summary="オンボーディング時にユーザーが回答した、属性・傾向に関する質問と回答を1件保存",
)
def create_preference(preference: PreferenceCreate, db: Session = Depends(get_db)):
    # ユーザー存在確認
    user_exists = db.query(User).filter(User.id == preference.user_id).first()
    if not user_exists:
        raise HTTPException(status_code=400, detail="指定されたユーザーが存在しません")
    
    # selected_answersリストをセミコロン区切りの文字列に変換
    selected_answers_str = ";".join(preference.selected_answers)
    
    # データベースにPreferenceレコードを作成
    db_preference = PreferenceModel(
        user_id=preference.user_id,
        question=preference.question,
        selected_answers=selected_answers_str
    )
    
    db.add(db_preference)
    db.commit()
    db.refresh(db_preference)
    
    # レスポンス用にスキーマ形式に変換
    return Preference(
        id=db_preference.id,
        user_id=db_preference.user_id,
        question=db_preference.question,
        selected_answers=db_preference.selected_answers.split(";") if db_preference.selected_answers else []
    )


@router.post(
    "/preferences", 
    response_model=List[Preference], 
    status_code=201,
    summary="オンボーディング時にユーザーが回答した、属性・傾向に関する質問と回答のリストを一括で保存",
)
def create_preferences(preferences: List[PreferenceCreate], db: Session = Depends(get_db)):
    created_preferences = []
    
    try:
        # 複数のPreferenceレコードを一括作成
        for preference in preferences:
            # ユーザー存在確認
            user_exists = db.query(User).filter(User.id == preference.user_id).first()
            if not user_exists:
                raise HTTPException(status_code=400, detail=f"ユーザーID {preference.user_id} が存在しません")
            
            # selected_answersリストをセミコロン区切りの文字列に変換
            selected_answers_str = ";".join(preference.selected_answers)
            
            db_preference = PreferenceModel(
                user_id=preference.user_id,
                question=preference.question,
                selected_answers=selected_answers_str
            )
            
            db.add(db_preference)
            created_preferences.append(db_preference)
        
        # 一括でコミット
        db.commit()
        
        # 作成されたレコードをレスポンス用に変換
        result = []
        for db_pref in created_preferences:
            db.refresh(db_pref)
            result.append(Preference(
                id=db_pref.id,
                user_id=db_pref.user_id,
                question=db_pref.question,
                selected_answers=db_pref.selected_answers.split(";") if db_pref.selected_answers else []
            ))
        
        return result
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="設定の保存に失敗しました")

@router.get(
    "/preferences", 
    response_model=List[Preference],
    summary="保存されているユーザーの属性・傾向に関する質問と回答のリストを取得",
)
def get_preferences(user_id: int = Query(..., description="ユーザーID", ge=1), db: Session = Depends(get_db)):
    # 指定されたユーザーIDのPreferenceレコードを取得
    db_preferences = db.query(PreferenceModel).filter(PreferenceModel.user_id == user_id).all()
    
    # レスポンス用にスキーマ形式に変換
    result = []
    for db_pref in db_preferences:
        result.append(Preference(
            id=db_pref.id,
            user_id=db_pref.user_id,
            question=db_pref.question,
            selected_answers=db_pref.selected_answers.split(";") if db_pref.selected_answers else []
        ))
    
    return result

@router.get(
    "/financial-report", 
    response_model=FinancialReport,
    summary="ユーザーの財務状況を分析し、インサイトと支出のカテゴリごとの合計金額を取得",
)
def get_financial_report(user_id: int = Query(..., description="ユーザーID", ge=1), db: Session = Depends(get_db)):
    """ユーザーの財務レポートを生成"""
    try:
        # サービスを取得
        financial_service = ServiceFactory.create_financial_service()
        openai_service = ServiceFactory.create_openai_service()
        
        # 財務データを取得
        financial_data = financial_service.generate_financial_report_data(user_id, db)
        
        # OpenAI サービスを使用して財務インサイトを生成
        insights = openai_service.generate_financial_insights(
            financial_data["user_preferences"], 
            financial_data["transactions"]
        )
        
        # レポートを構築
        report = {
            "user_id": user_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "insights": insights,
            "expenses_by_category": financial_data["expenses_by_category"]
        }
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"財務レポートの生成に失敗しました: {str(e)}")

@router.get(
    "/recommended_recipes", 
    response_model=List[RecipeTemplateWithUserAndRuleTemplatesWithTriggerAndAction],
    summary="ユーザーに対し導入が推奨されるレシピテンプレート(ルールテンプレートを含む)を取得",
)
def get_recommend_recipe_templates(user_id: int = Query(..., description="ユーザーID", ge=1), db: Session = Depends(get_db)):
    """ユーザーに推奨されるレシピテンプレートを取得"""
    try:
        # レシピ推奨サービスを取得
        recipe_service = ServiceFactory.create_recipe_recommendation_service()
        
        # 推奨レシピを取得
        return recipe_service.get_recommended_recipes_for_user(user_id, db)
        
    except ValueError as e:
        # ユーザーが存在しない場合
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        # サービス層でのエラー
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # 予期しないエラー
        raise HTTPException(status_code=500, detail=f"推奨レシピの取得に失敗しました: {str(e)}")