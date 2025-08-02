from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Preference as PreferenceModel, User
from schemas import PreferenceCreate, Preference
from typing import List

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
