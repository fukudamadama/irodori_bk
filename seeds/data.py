"""
統合シードデータファイル
基本マスタデータ、サンプルユーザー、サンプルレシピ、サンプルルールの全てを含む
"""

from datetime import datetime, timezone, date
from sqlalchemy.orm import Session
from database import SessionLocal
from models import (
    User, Trigger, Action, RuleTemplate, RecipeTemplate, 
    RecipeTemplateRuleTemplate, Preference
)
from enums import RuleCategory
import bcrypt

# ===== サンプルトリガー・アクション関連 =====

def seed_sample_triggers(session_maker=None):
    if session_maker is None:
        session_maker = SessionLocal
    
    db = session_maker()
    try:
        insert_sample_triggers(db)
        db.commit()
    except Exception as e:
        print(f"サンプルトリガーデータ投入エラー: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def insert_sample_triggers(db: Session):
    triggers_data = [
        {
            "id": 1,
            "name": "定期実行 (毎週)",
            "description": "指定した曜日に毎週トリガーを実行します。",
            "required_params": {
                "day_of_week": "string"
            }
        },
        {
            "id": 2,
            "name": "定期実行 (月末)",
            "description": "毎月、月の最終日にトリガーを実行します。",
            "required_params": {}
        },
        {
            "id": 3,
            "name": "支出発生",
            "description": "金額やカテゴリを問わず、全ての支出を検知します。",
            "required_params": {}
        },
        {
            "id": 4,
            "name": "特定カテゴリでの支出",
            "description": "指定したカテゴリでの支出を検知します。",
            "required_params": {
                "categories": [
                    "string"
                ]
            }
        },
        {
            "id": 5,
            "name": "給与・賞与の入金",
            "description": "特定のキーワードを含む入金を検知します。",
            "required_params": {
                "keyword": "string"
            }
        },
        {
            "id": 6,
            "name": "条件付き支出",
            "description": "指定カテゴリの支出が、設定した金額を超えた場合に検知します。",
            "required_params": {
                "category": "string",
                "operator": ">",
                "amount": "number"
            }
        },
        {
            "id": 8,
            "name": "カテゴリ支出ゼロの日",
            "description": "指定したカテゴリでの支出が一日ゼロだった場合に検知します。",
            "required_params": {
                "categories": [
                    "string"
                ]
            }
        }
    ]
    
    for trigger_data in triggers_data:
        # 既存データをチェック
        existing = db.query(Trigger).filter(Trigger.id == trigger_data["id"]).first()
        if not existing:
            trigger = Trigger(**trigger_data)
            db.add(trigger)
    
    print(f"トリガーデータ {len(triggers_data)} 件投入完了")

def seed_sample_actions(session_maker=None):
    if session_maker is None:
        session_maker = SessionLocal
    
    db = session_maker()
    try:
        insert_sample_actions(db)
        db.commit()
    except Exception as e:
        print(f"サンプルアクションデータ投入エラー: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def insert_sample_actions(db: Session):
    actions_data = [
        {
            "id": 101,
            "name": "固定額を貯金/投資",
            "description": "指定した固定額を、別の口座へ移します。",
            "required_params": {
                "amount": "number",
                "destination_account": "string"
            }
        },
        {
            "id": 102,
            "name": "支出額の割合を貯金/投資",
            "description": "支出額の指定割合を、別の口座へ移します。",
            "required_params": {
                "percentage": "number",
                "destination_account": "string"
            }
        },
        {
            "id": 103,
            "name": "収入額の割合を貯金/投資",
            "description": "入金額の指定割合を、別の口座へ移します。",
            "required_params": {
                "percentage": "number",
                "destination_account": "string"
            }
        },
        {
            "id": 104,
            "name": "口座残高の割合を貯金",
            "description": "指定口座の残高から指定割合を、別の口座へ移します。",
            "required_params": {
                "percentage": "number",
                "source_account": "string",
                "destination_account": "string"
            }
        },
        {
            "id": 105,
            "name": "差額をペナルティ貯金",
            "description": "支出額と基準額の差額を計算し、強制的に別口座へ移します。",
            "required_params": {
                "base_amount": "number",
                "destination_account": "string"
            }
        },
        {
            "id": 106,
            "name": "固定額をごほうび貯金",
            "description": "指定した固定額を、ご褒美として別口座へ移します。",
            "required_params": {
                "amount": "number",
                "destination_account": "string"
            }
        }
    ]
    
    for action_data in actions_data:
        # 既存データをチェック
        existing = db.query(Action).filter(Action.id == action_data["id"]).first()
        if not existing:
            action = Action(**action_data)
            db.add(action)
    
    print(f"アクションデータ {len(actions_data)} 件投入完了")

# ===== サンプルユーザー関連 =====

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def seed_sample_users(session_maker=None):
    if session_maker is None:
        session_maker = SessionLocal
    
    db = session_maker()
    try:
        create_sample_users(db)
        db.commit()
    except Exception as e:
        print(f"サンプルユーザーデータ投入エラー: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_sample_users(db: Session):
    current_time = datetime.now(timezone.utc)
    
    users_raw_data = [
        {
            "id": 1,
            "last_name": "ちょー",
            "first_name": "りじ",
            "email": "riricho@example.com",
            "birthdate": date(1998, 7, 15),
            "postal_code": "185-0021",
            "address": "東京都国分寺市南町3-20-3",
            "phone_number": "080-1111-2222",
            "occupation": "デザイナー",
            "company_name": "株式会社CreativeStyle",
            "password": "abc123"
        },
        {
            "id": 2,
            "last_name": "はと",
            "first_name": "ちゃん",
            "email": "hato.tanaka@example.com",
            "birthdate": date(1995, 4, 1),
            "postal_code": "150-0002",
            "address": "東京都渋谷区渋谷2-24-12",
            "phone_number": "090-3333-4444",
            "occupation": "会社員",
            "company_name": "株式会社テックフロント",
            "password": "def456"
        },
        {
            "id": 3,
            "last_name": "熱い",
            "first_name": "JSON",
            "email": "atsui.json@example.com",
            "birthdate": date(2001, 11, 10),
            "postal_code": "160-0023",
            "address": "東京都新宿区西新宿2-8-1",
            "phone_number": "070-5555-6666",
            "occupation": "エンジニア",
            "company_name": "株式会社データドリブン",
            "password": "ghi789"
        }
    ]
    
    for user_raw_data in users_raw_data:
        # 既存データをチェック
        existing = db.query(User).filter(User.id == user_raw_data["id"]).first()
        if not existing:
            # パスワードをハッシュ化し、日付フィールドを追加
            user_data = user_raw_data.copy()
            user_data["password_hash"] = hash_password(user_raw_data["password"])
            del user_data["password"]  # 元のpasswordフィールドを削除
            user_data["created_at"] = current_time
            
            user = User(**user_data)
            db.add(user)
    
    print(f"サンプルユーザー {len(users_raw_data)} 件投入完了")

# ===== サンプルルール関連 =====

def seed_sample_rules(session_maker=None):
    
    if session_maker is None:
        session_maker = SessionLocal
    
    db = session_maker()
    try:
        insert_sample_rule_templates(db)
        db.commit()
    except Exception as e:
        print(f"サンプルルールテンプレートデータ投入エラー: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def insert_sample_rule_templates(db: Session):
    current_time = datetime.now(timezone.utc)
    
    rule_templates_data = [
        {
            "id": 1001,
            "name": "毎月の収入の10%を貯金",
            "description": "「給与」というキーワードの入金をトリガーに、その金額の10%を自動で貯金口座へ移すルールです。",
            "category": RuleCategory.INCREASE_SAVINGS,
            "author_id": 1,
            "trigger_id": 5,
            "trigger_params": {
                "keyword": "給与"
            },
            "action_id": 103,
            "action_params": {
                "percentage": 10,
                "destination_account": "savings"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1002,
            "name": "月末に残った金額の10%を「おつり貯金」",
            "description": "毎月末にメイン口座の残高を確認し、その10%を貯金口座へ自動で移すルールです。",
            "category": RuleCategory.INCREASE_SAVINGS,
            "author_id": 2,
            "trigger_id": 2,
            "trigger_params": {},
            "action_id": 104,
            "action_params": {
                "percentage": 10,
                "source_account": "primary",
                "destination_account": "savings"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1003,
            "name": "毎週500円ずつ自動で貯金",
            "description": "毎週日曜日に、自動で500円を貯金口座へ積み立てるルールです。",
            "category": RuleCategory.INCREASE_SAVINGS,
            "author_id": 2,
            "trigger_id": 1,
            "trigger_params": {
                "day_of_week": "Sunday"
            },
            "action_id": 101,
            "action_params": {
                "amount": 500,
                "destination_account": "savings"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1004,
            "name": "支出の1%を自動で貯金（例：コンビニで300円→3円貯金）",
            "description": "全ての支出をトリガーに、その金額の1%を自動で貯金口座へ移すルールです。",
            "category": RuleCategory.INCREASE_SAVINGS,
            "author_id": 2,
            "trigger_id": 3,
            "trigger_params": {},
            "action_id": 102,
            "action_params": {
                "percentage": 1,
                "destination_account": "savings"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1005,
            "name": "推し活・好きなことに使った金額の10%を貯金",
            "description": "「推し活」「エンタメ」カテゴリでの支出をトリガーに、その金額の10%を自動で貯金口座へ移すルールです。",
            "category": RuleCategory.INCREASE_SAVINGS,
            "author_id": 3,
            "trigger_id": 4,
            "trigger_params": {
                "categories": [
                    "推し活",
                    "エンタメ"
                ]
            },
            "action_id": 102,
            "action_params": {
                "percentage": 10,
                "destination_account": "savings"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1006,
            "name": "毎月の給与から30,000円をNISAで全世界株式を購入",
            "description": "「給与」というキーワードの入金をトリガーに、毎月固定で30,000円を投資用口座へ自動で振り替えるルールです。",
            "category": RuleCategory.ASSET_MANAGEMENT,
            "author_id": 3,
            "trigger_id": 5,
            "trigger_params": {
                "keyword": "給与"
            },
            "action_id": 101,
            "action_params": {
                "amount": 30000,
                "destination_account": "investment_nisa"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1007,
            "name": "お昼のランチ代を700円以内にする",
            "description": "「食費-ランチ」カテゴリでの支出が700円を超えた場合、その超過分を強制的にペナルティ口座へ移すルールです。",
            "category": RuleCategory.REDUCE_EXPENSES,
            "author_id": 2,
            "trigger_id": 6,
            "trigger_params": {
                "category": "食費-ランチ",
                "operator": ">",
                "amount": 700
            },
            "action_id": 105,
            "action_params": {
                "base_amount": 700,
                "destination_account": "penalty_savings"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1008,
            "name": "減らした分は自動で「目標貯金」へ移動",
            "description": "「コンビニ」「カフェ」カテゴリでの支出がゼロだった日に、節約達成のご褒美として自動で150円を貯金するルールです。",
            "category": RuleCategory.REDUCE_EXPENSES,
            "author_id": 1,
            "trigger_id": 8,
            "trigger_params": {
                "categories": [
                    "コンビニ",
                    "カフェ"
                ]
            },
            "action_id": 106,
            "action_params": {
                "amount": 150,
                "destination_account": "habit_savings"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        }
    ]
    
    for rule_template_data in rule_templates_data:
        # 既存データをチェック
        existing = db.query(RuleTemplate).filter(RuleTemplate.id == rule_template_data["id"]).first()
        if not existing:
            rule_template = RuleTemplate(**rule_template_data)
            db.add(rule_template)
    
    print(f"ルールテンプレート {len(rule_templates_data)} 件投入完了")

# ===== サンプルレシピ関連 =====

def seed_sample_recipes(session_maker=None):
    if session_maker is None:
        session_maker = SessionLocal
    
    db = session_maker()
    try:
        insert_sample_recipe_templates(db)
        insert_sample_recipe_rule_relations(db)
        db.commit()
    except Exception as e:
        print(f"サンプルレシピテンプレートデータ投入エラー: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def insert_sample_recipe_templates(db: Session):
    current_time = datetime.now(timezone.utc)
    
    recipe_templates_data = [
        {
            "id": 201,
            "name": "ジュースを水に変える魔法",
            "description": "日々の小さな浪費を見直したい人！",
            "author_id": 1,
            "is_public": True,
            "likes_count": 112,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 202,
            "name": "ヒヨコ貯金チャレンジ",
            "description": "日々の小さな浪費を見直したい人！",
            "author_id": 2,
            "is_public": True,
            "likes_count": 200,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 203,
            "name": "WHY 浪費 PEOPLE ! ? 🔥",
            "description": "ストイックに節約し資産形成！",
            "author_id": 3,
            "is_public": True,
            "likes_count": 5,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        }
    ]
    
    for recipe_template_data in recipe_templates_data:
        # 既存データをチェック
        existing = db.query(RecipeTemplate).filter(RecipeTemplate.id == recipe_template_data["id"]).first()
        if not existing:
            recipe_template = RecipeTemplate(**recipe_template_data)
            db.add(recipe_template)
    
    print(f"レシピテンプレート {len(recipe_templates_data)} 件投入完了")

def insert_sample_recipe_rule_relations(db: Session):
    relations_data = [
        {
            "recipe_template_id": 201,
            "rule_template_id": 1001
        },
        {
            "recipe_template_id": 201,
            "rule_template_id": 1008
        },
        {
            "recipe_template_id": 202,
            "rule_template_id": 1002
        },
        {
            "recipe_template_id": 202,
            "rule_template_id": 1003
        },
        {
            "recipe_template_id": 202,
            "rule_template_id": 1004
        },
        {
            "recipe_template_id": 202,
            "rule_template_id": 1007
        },
        {
            "recipe_template_id": 203,
            "rule_template_id": 1005
        },
        {
            "recipe_template_id": 203,
            "rule_template_id": 1006
        }
    ]
    
    for relation_data in relations_data:
        # 既存データをチェック
        existing = db.query(RecipeTemplateRuleTemplate).filter(
            RecipeTemplateRuleTemplate.recipe_template_id == relation_data["recipe_template_id"],
            RecipeTemplateRuleTemplate.rule_template_id == relation_data["rule_template_id"]
        ).first()
        if not existing:
            relation = RecipeTemplateRuleTemplate(**relation_data)
            db.add(relation)
    
    print(f"レシピ-ルール関連付け {len(relations_data)} 件投入完了")

# ===== サンプルプリファレンス関連 =====

def seed_sample_preferences(session_maker=None):
    if session_maker is None:
        session_maker = SessionLocal
    
    db = session_maker()
    try:
        create_sample_preferences(db)
        db.commit()
    except Exception as e:
        print(f"サンプルユーザープリファレンスデータ投入エラー: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_sample_preferences(db: Session):
    preferences_data = [
        {
            "user_id": 2,
            "question": "あなたの推しはなにブヒ？",
            "selected_answers": "アニメ;インフルエンサー"
        },
        {
            "user_id": 2,
            "question": "推し活の内容はなにブヒ？",
            "selected_answers": "グッズ購入;サブスク利用"
        },
        {
            "user_id": 2,
            "question": "今や将来の生活のための備えができているブヒか？",
            "selected_answers": "貯金もあんまりないしちょっと不安ブヒ"
        },
        {
            "user_id": 2,
            "question": "月に自由に使えるお金はいくらくらいブヒ？",
            "selected_answers": "5,000円〜9,999円"
        },
        {
            "user_id": 2,
            "question": "お金の目標を設定するブヒ",
            "selected_answers": "結婚や出産、子育てのためにお金を貯めたいブヒ"
        },
        {
            "user_id": 2,
            "question": "家族構成を教えてブヒ",
            "selected_answers": "一人暮らし"
        },
        {
            "user_id": 2,
            "question": "今支払いに使っているカードと銀行を教えてブヒ",
            "selected_answers": "三友カード;三友銀行"
        }
    ]
    
    for pref_data in preferences_data:
        # 既存データをチェック（同じユーザー・質問の組み合わせ）
        existing = db.query(Preference).filter(
            Preference.user_id == pref_data["user_id"],
            Preference.question == pref_data["question"]
        ).first()
        if not existing:
            preference = Preference(
                user_id=pref_data["user_id"],
                question=pref_data["question"],
                selected_answers=pref_data["selected_answers"],
                created_at=datetime.now(timezone.utc)
            )
            db.add(preference)
    
    print(f"サンプルユーザープリファレンス {len(preferences_data)} 件投入完了")