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
        },
        {
            "id": 9,
            "name": "ガチャタイム（支出発生時ランダム）",
            "description": "任意の支出が発生した時に一定確率でトリガーを実行します。",
            "required_params": {
                "trigger_probability": "number"
            }
        },
        {
            "id": 10,
            "name": "レベルアップ検知",
            "description": "累計貯金額が一定の閾値に達した時にトリガーを実行します。",
            "required_params": {
                "threshold_amount": "number"
            }
        },
        {
            "id": 11,
            "name": "時空の歪み（特定時刻）",
            "description": "毎日指定した時刻にタイムトラベルトリガーを実行します。",
            "required_params": {
                "hour": "number",
                "minute": "number"
            }
        },
        {
            "id": 12,
            "name": "推し活同額ミラーリング",
            "description": "推し活関連カテゴリでの支出と同額の条件をトリガーします。",
            "required_params": {
                "mirror_categories": [
                    "string"
                ]
            }
        },
        {
            "id": 13,
            "name": "推し活マイルストーン接近",
            "description": "推しの生誕祭やライブなどの大切な日まで指定日数になった時にトリガーします。",
            "required_params": {
                "event_name": "string",
                "days_before": "number"
            }
        },
        {
            "id": 14,
            "name": "断捨離リマインダー",
            "description": "定期的に推し活グッズの見直しを促すトリガーです。",
            "required_params": {
                "interval_weeks": "number"
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
        },
        {
            "id": 107,
            "name": "ガチャ抽選貯金",
            "description": "ランダムな金額（指定範囲内）を貯金口座へ移します。",
            "required_params": {
                "min_amount": "number",
                "max_amount": "number",
                "destination_account": "string"
            }
        },
        {
            "id": 108,
            "name": "宇宙船建造費積立",
            "description": "支出額と同額を「火星移住基金」へ自動積立します。",
            "required_params": {
                "destination_account": "string"
            }
        },
        {
            "id": 109,
            "name": "ドラゴン討伐EXP獲得",
            "description": "支出額の一定割合をEXP（貯金）として獲得し、レベルアップボーナスも付与します。",
            "required_params": {
                "exp_percentage": "number",
                "level_bonus": "number",
                "destination_account": "string"
            }
        },
        {
            "id": 110,
            "name": "時空分散投資",
            "description": "指定金額を過去・現在・未来の3つの口座に分散投資します。",
            "required_params": {
                "amount": "number",
                "past_account": "string",
                "present_account": "string",
                "future_account": "string"
            }
        },
        {
            "id": 111,
            "name": "推しと共に成長投資",
            "description": "推し活支出額と同額を「推し成長ファンド」へ投資します。",
            "required_params": {
                "destination_account": "string",
                "growth_multiplier": "number"
            }
        },
        {
            "id": 112,
            "name": "マイルストーン達成ボーナス",
            "description": "推し活イベントまでの日数に応じてボーナス貯金を実行します。",
            "required_params": {
                "bonus_per_day": "number",
                "destination_account": "string"
            }
        },
        {
            "id": 113,
            "name": "断捨離売上投資",
            "description": "推し活グッズの売上金を自動で投資口座へ移します。",
            "required_params": {
                "sale_amount": "number",
                "investment_ratio": "number",
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
        },
        {
            "id": 1009,
            "name": "🎰 運命のガチャ貯金",
            "description": "支出するたびに30%の確率でガチャが発動！1円〜1000円のランダム貯金でドキドキワクワク！",
            "category": RuleCategory.INCREASE_SAVINGS,
            "author_id": 1,
            "trigger_id": 9,
            "trigger_params": {
                "trigger_probability": 30
            },
            "action_id": 107,
            "action_params": {
                "min_amount": 1,
                "max_amount": 1000,
                "destination_account": "gacha_savings"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1010,
            "name": "🚀 地球最後の楽しみ貯金",
            "description": "全ての支出を「地球での最後の楽しみ」として、同額を火星移住基金へ積立！地球を去る日のために！",
            "category": RuleCategory.INCREASE_SAVINGS,
            "author_id": 2,
            "trigger_id": 3,
            "trigger_params": {},
            "action_id": 108,
            "action_params": {
                "destination_account": "mars_fund"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1011,
            "name": "⚔️ 魔物討伐でEXP獲得",
            "description": "支出という名の魔物を倒すたびに5%のEXPを獲得！勇者として成長しながら資産も増やそう！",
            "category": RuleCategory.INCREASE_SAVINGS,
            "author_id": 3,
            "trigger_id": 3,
            "trigger_params": {},
            "action_id": 109,
            "action_params": {
                "exp_percentage": 5,
                "level_bonus": 500,
                "destination_account": "hero_savings"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1012,
            "name": "🏆 レベルアップボーナス",
            "description": "貯金額が10万円に達するたびにレベルアップ！勇者への道のりで特別ボーナス獲得！",
            "category": RuleCategory.INCREASE_SAVINGS,
            "author_id": 3,
            "trigger_id": 10,
            "trigger_params": {
                "threshold_amount": 100000
            },
            "action_id": 106,
            "action_params": {
                "amount": 5000,
                "destination_account": "hero_bonus"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1013,
            "name": "⏰ 時空分散投資術",
            "description": "毎日午後2時にタイムマシン起動！3000円を過去・現在・未来に均等分散投資でタイムパラドックス回避！",
            "category": RuleCategory.ASSET_MANAGEMENT,
            "author_id": 1,
            "trigger_id": 11,
            "trigger_params": {
                "hour": 14,
                "minute": 0
            },
            "action_id": 110,
            "action_params": {
                "amount": 3000,
                "past_account": "past_investment",
                "present_account": "present_savings",
                "future_account": "future_fund"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1014,
            "name": "💎 推しと共に輝く投資",
            "description": "推し活に使った金額と同額×1.5倍を「推し成長ファンド」へ投資！推しと一緒に資産も成長させよう！",
            "category": RuleCategory.ASSET_MANAGEMENT,
            "author_id": 2,
            "trigger_id": 12,
            "trigger_params": {
                "mirror_categories": [
                    "推し活",
                    "エンタメ",
                    "グッズ"
                ]
            },
            "action_id": 111,
            "action_params": {
                "destination_account": "oshi_growth_fund",
                "growth_multiplier": 1.5
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1015,
            "name": "🎯 推し生誕祭カウントダウン貯金",
            "description": "推しの生誕祭まで30日前からカウントダウン！毎日50円×残り日数分のボーナス貯金でお祝い資金を準備！",
            "category": RuleCategory.INCREASE_SAVINGS,
            "author_id": 1,
            "trigger_id": 13,
            "trigger_params": {
                "event_name": "推し生誕祭",
                "days_before": 30
            },
            "action_id": 112,
            "action_params": {
                "bonus_per_day": 50,
                "destination_account": "birthday_fund"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1016,
            "name": "🎪 ライブ遠征積立貯金",
            "description": "ライブまで7日前から緊急積立開始！毎日100円×残り日数分で遠征費をしっかり確保！",
            "category": RuleCategory.INCREASE_SAVINGS,
            "author_id": 1,
            "trigger_id": 13,
            "trigger_params": {
                "event_name": "ライブ遠征",
                "days_before": 7
            },
            "action_id": 112,
            "action_params": {
                "bonus_per_day": 100,
                "destination_account": "live_fund"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1017,
            "name": "🗑️ 推し活グッズ断捨離で投資",
            "description": "2週間ごとの断捨離リマインダーで不要グッズを売却！売上の80%を自動で投資に回して真の推し活資金を作る！",
            "category": RuleCategory.ASSET_MANAGEMENT,
            "author_id": 3,
            "trigger_id": 14,
            "trigger_params": {
                "interval_weeks": 2
            },
            "action_id": 113,
            "action_params": {
                "sale_amount": 5000,
                "investment_ratio": 80,
                "destination_account": "oshi_investment"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1018,
            "name": "💎 厳選推し活ファンド",
            "description": "月1回の断捨離で本当に必要な推し活を見極め！売上の全額を「厳選推し活ファンド」として長期投資へ！",
            "category": RuleCategory.ASSET_MANAGEMENT,
            "author_id": 3,
            "trigger_id": 14,
            "trigger_params": {
                "interval_weeks": 4
            },
            "action_id": 113,
            "action_params": {
                "sale_amount": 10000,
                "investment_ratio": 100,
                "destination_account": "select_oshi_fund"
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
            "description": "【推し活で財布がピンチな人向け・ゆるめ】コンビニでの無意識な浪費を見直したい人におすすめ！少しずつでも変化を実感できる優しいレシピ",
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
            "description": "【推し活初心者向け・ゆるめ】推しにお金を使いすぎて貯金ゼロの人でも大丈夫！小額からコツコツ始められる可愛い貯金術",
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
            "description": "【推し活ガチ勢向け・ストイック】推しへの愛は変えずに無駄遣いを徹底カット！本気で資産形成したい推し活民のための鬼レシピ",
            "author_id": 3,
            "is_public": True,
            "likes_count": 5,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 204,
            "name": "🎰 ガチャ貯金システム 🎰",
            "description": "【推し活ガチャ好き向け・ゆるめ】課金感覚で楽しく貯金！支出するたびにランダム貯金で運試し。推しのガチャ資金も貯まる一石二鳥システム",
            "author_id": 1,
            "is_public": True,
            "likes_count": 347,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 205,
            "name": "🚀 火星移住計画貯金 🚀",
            "description": "【推し活で現実逃避したい人向け・ストイック】地球での推し活を「最後の楽しみ」として同額貯金。壮大な目標で楽しく節約意識を高める",
            "author_id": 2,
            "is_public": True,
            "likes_count": 89,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 206,
            "name": "🐉 ドラゴン討伐家計術 ⚔️",
            "description": "【推し活ゲーマー向け・ストイック】支出を倒すべき敵として攻略！レベルアップ要素で推し活資金も確実に増やすRPG式家計管理",
            "author_id": 3,
            "is_public": True,
            "likes_count": 156,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 207,
            "name": "⏰ タイムトラベラー投資術 ⏰",
            "description": "【推し活で将来不安な人向け・ストイック】過去・現在・未来の3つの時間軸で資産管理。SF好きな推し活民が楽しく長期投資できる仕組み",
            "author_id": 1,
            "is_public": True,
            "likes_count": 234,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 208,
            "name": "🌸 推しと共に成長する資産形成 💎",
            "description": "【推し活で罪悪感がある人向け・ゆるめ】推しへの愛と同じ分だけ自分にも投資！推し活を諦めずに資産も増やす究極の両立術",
            "author_id": 2,
            "is_public": True,
            "likes_count": 445,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 209,
            "name": "💰 推し活マイルストーン貯金 🎯",
            "description": "【推し活で目標が欲しい人向け・ゆるめ】推しの生誕祭やライブまでの期間を活用した目標設定型貯金。推し活イベントが貯金のモチベーションに変わる！",
            "author_id": 1,
            "is_public": True,
            "likes_count": 78,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 210,
            "name": "⚡ 推し活断捨離チャレンジ 🗑️",
            "description": "【推し活グッズが溢れてる人向け・ストイック】不要な推し活グッズを売って投資資金に！「真の推し活」を見極めて資産と愛を両方増やす断捨離術",
            "author_id": 3,
            "is_public": True,
            "likes_count": 23,
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
        },
        # 🎰 ガチャ貯金システム
        {
            "recipe_template_id": 204,
            "rule_template_id": 1009
        },
        {
            "recipe_template_id": 204,
            "rule_template_id": 1004
        },
        # 🚀 火星移住計画貯金
        {
            "recipe_template_id": 205,
            "rule_template_id": 1010
        },
        {
            "recipe_template_id": 205,
            "rule_template_id": 1001
        },
        # 🐉 ドラゴン討伐家計術
        {
            "recipe_template_id": 206,
            "rule_template_id": 1011
        },
        {
            "recipe_template_id": 206,
            "rule_template_id": 1012
        },
        {
            "recipe_template_id": 206,
            "rule_template_id": 1007
        },
        # ⏰ タイムトラベラー投資術
        {
            "recipe_template_id": 207,
            "rule_template_id": 1013
        },
        {
            "recipe_template_id": 207,
            "rule_template_id": 1006
        },
        # 🌸 推しと共に成長する資産形成
        {
            "recipe_template_id": 208,
            "rule_template_id": 1014
        },
        {
            "recipe_template_id": 208,
            "rule_template_id": 1005
        },
        # 💰 推し活マイルストーン貯金
        {
            "recipe_template_id": 209,
            "rule_template_id": 1015
        },
        {
            "recipe_template_id": 209,
            "rule_template_id": 1016
        },
        # ⚡ 推し活断捨離チャレンジ
        {
            "recipe_template_id": 210,
            "rule_template_id": 1017
        },
        {
            "recipe_template_id": 210,
            "rule_template_id": 1018
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