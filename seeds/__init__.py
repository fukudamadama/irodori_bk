"""
シードデータ管理パッケージ

使用例:
- from seeds import seed_all_data
- from seeds.data import seed_base_data  # 直接インポート
"""

from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from database import SessionLocal, engine, SQLALCHEMY_DATABASE_URL
from models import (
    Base, User, Trigger, Action, RuleTemplate, RecipeTemplate, 
    RecipeTemplateRuleTemplate, Rule, Recipe, RecipeRule, Preference
)
from .data import seed_sample_triggers, seed_sample_actions, seed_sample_users, seed_sample_rules, seed_sample_recipes, seed_sample_preferences

def seed_sample_data(clear_existing=True):
    # seed専用のecho=Falseのengineを作成
    if SQLALCHEMY_DATABASE_URL.startswith("mysql"):
        silent_engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)
    else:
        silent_engine = create_engine(
            SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, echo=False
        )
    
    # seed専用のSessionMakerを作成
    SilentSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=silent_engine)
    
    # データベース接続
    db = SilentSessionLocal()
    
    try:
        # テーブル作成
        Base.metadata.create_all(bind=silent_engine)
        
        # 既存データ削除（オプション）
        if clear_existing:
            clear_existing_data(db)
        
        # シードデータ投入（専用SessionMakerを渡す）
        seed_sample_triggers(SilentSessionLocal)
        seed_sample_actions(SilentSessionLocal)
        seed_sample_users(SilentSessionLocal)
        seed_sample_rules(SilentSessionLocal)
        seed_sample_recipes(SilentSessionLocal)
        seed_sample_preferences(SilentSessionLocal)
             
    except Exception as e:
        print(f"サンプルシードデータ投入エラー: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def clear_existing_data(db: Session):
    
    # プリファレンステーブルを削除
    db.query(Preference).delete()
    
    # 関連テーブルから削除
    db.query(RecipeTemplateRuleTemplate).delete()
    db.query(RecipeRule).delete()
    
    # メインテーブルを削除
    db.query(Recipe).delete()
    db.query(Rule).delete()
    db.query(RuleTemplate).delete()
    db.query(RecipeTemplate).delete()
    db.query(Action).delete()
    db.query(Trigger).delete()
    
    # サンプルユーザーとデモユーザーを削除
    db.query(User).filter(User.id.in_([1, 2])).delete()
    
    db.commit()
    print("既存データの削除完了")
