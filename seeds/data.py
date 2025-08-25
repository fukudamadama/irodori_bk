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
        },
        {
            "id": 15,
            "name": "SNSライブ配信コメント",
            "description": "推しのライブ配信にコメントした時にトリガーを実行します。",
            "required_params": {
                "sns_platform": "string",
                "streamer_name": "string"
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
        },
        {
            "id": 114,
            "name": "固定額寄付",
            "description": "指定した固定額を指定の寄付先へ送金します。",
            "required_params": {
                "amount": "number",
                "donation_recipient": "string",
                "cause_category": "string"
            }
        },
        {
            "id": 115,
            "name": "支出額割合投資",
            "description": "支出額の指定割合を指定のETFや投資商品に自動投資します。",
            "required_params": {
                "percentage": "number",
                "investment_product": "string",
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
            "last_name": "はまだ",
            "first_name": "りじちょー",
            "email": "riricho@example.com",
            "birthdate": date(1998, 7, 15),
            "postal_code": "185-0021",
            "address": "東京都国分寺市西町3-20-3",
            "phone_number": "080-1111-2222",
            "occupation": "デザイナー",
            "company_name": "株式会社CreativeStyle",
            "nickname": "りじちょー",
            "password": "abc123"
        },
        {
            "id": 2,
            "last_name": "はと",
            "first_name": "ちか",
            "email": "hato.tanaka@example.com",
            "birthdate": date(1995, 4, 1),
            "postal_code": "150-0002",
            "address": "東京都渋谷区渋谷2-24-12",
            "phone_number": "090-3333-4444",
            "occupation": "会社員",
            "company_name": "株式会社テックフロント",
            "nickname": "はとちゃん",
            "password": "def456"
        },
        {
            "id": 3,
            "last_name": "厚切り",
            "first_name": "ジェーソン",
            "email": "atsui.json@example.com",
            "birthdate": date(2001, 11, 10),
            "postal_code": "160-0023",
            "address": "東京都新宿区西新宿2-8-1",
            "phone_number": "070-5555-6666",
            "occupation": "エンジニア",
            "company_name": "株式会社データドリブン",
            "nickname": "熱いJSON",
            "password": "ghi789"
        },
        {
            "id": 4,
            "last_name": "みら",
            "first_name": "しずか",
            "email": "mira.shizuka@example.com",
            "birthdate": date(1999, 3, 5),
            "postal_code": "220-0012",
            "address": "神奈川県横浜市西区みなとみらい2-2-1",
            "phone_number": "090-7777-8888",
            "occupation": "学生",
            "company_name": "横浜国立大学",
            "nickname": "みらしー",
            "password": "jkl012"
        },
        {
            "id": 5,
            "last_name": "おし",
            "first_name": "あい",
            "email": "oshi.ai@example.com",
            "birthdate": date(1997, 8, 20),
            "postal_code": "540-0008",
            "address": "大阪府大阪市中央区大手前1-3-49",
            "phone_number": "080-9999-0000",
            "occupation": "公務員",
            "company_name": "大阪府庁",
            "nickname": "おしあい",
            "password": "mno345"
        },
        {
            "id": 6,
            "last_name": "がちゃ",
            "first_name": "らっきー",
            "email": "gacha.lucky@example.com",
            "birthdate": date(2002, 12, 31),
            "postal_code": "460-0003",
            "address": "愛知県名古屋市中区錦3-6-15",
            "phone_number": "070-1111-2222",
            "occupation": "フリーター",
            "company_name": "株式会社アルバイター",
            "nickname": "がちゃらき",
            "password": "pqr678"
        },
        {
            "id": 7,
            "last_name": "せつやく",
            "first_name": "まさる",
            "email": "setsuyaku.masaru@example.com",
            "birthdate": date(1985, 5, 15),
            "postal_code": "810-0001",
            "address": "福岡県福岡市中央区天神1-11-17",
            "phone_number": "092-3333-4444",
            "occupation": "会社員",
            "company_name": "九州商事株式会社",
            "nickname": "せつやく王",
            "password": "stu901"
        },
        {
            "id": 8,
            "last_name": "とうし",
            "first_name": "みらい",
            "email": "toushi.mirai@example.com",
            "birthdate": date(1992, 9, 8),
            "postal_code": "980-0811",
            "address": "宮城県仙台市青葉区一番町3-7-1",
            "phone_number": "022-5555-6666",
            "occupation": "金融業",
            "company_name": "東北ファイナンス株式会社",
            "nickname": "未来投資家",
            "password": "vwx234"
        },
        {
            "id": 9,
            "last_name": "こつこつ",
            "first_name": "はな",
            "email": "kotsukotsu.hana@example.com",
            "birthdate": date(2000, 2, 14),
            "postal_code": "760-0023",
            "address": "香川県高松市寿町2-1-1",
            "phone_number": "087-7777-8888",
            "occupation": "看護師",
            "company_name": "高松総合病院",
            "nickname": "はなコツ",
            "password": "yz2567"
        },
        {
            "id": 10,
            "last_name": "りじゅあ",
            "first_name": "らいふ",
            "email": "rejua.life@example.com",
            "birthdate": date(1988, 6, 25),
            "postal_code": "700-0901",
            "address": "岡山県岡山市北区本町6-36",
            "phone_number": "086-9999-0000",
            "occupation": "自営業",
            "company_name": "ライフバランス工房",
            "nickname": "りじゅ",
            "password": "abc890"
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
        },
        {
            "id": 1019,
            "name": "🌍 SNS連動寄付",
            "description": "推しのライブ配信にコメントするたびに100円を環境団体へ自動寄付！推し活と社会貢献を両立させる新しいカタチ！",
            "category": RuleCategory.INCREASE_SAVINGS,
            "author_id": 2,
            "trigger_id": 15,
            "trigger_params": {
                "sns_platform": "YouTube",
                "streamer_name": "推し配信者"
            },
            "action_id": 114,
            "action_params": {
                "amount": 100,
                "donation_recipient": "環境保護団体",
                "cause_category": "環境保護"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1020,
            "name": "🌱 サステナブル自動投資",
            "description": "サステナブル認証商品の購入額の20%を環境関連ETFに自動投資！地球に優しい買い物で未来への投資も実現！",
            "category": RuleCategory.ASSET_MANAGEMENT,
            "author_id": 1,
            "trigger_id": 4,
            "trigger_params": {
                "categories": [
                    "サステナブル商品",
                    "エコ商品",
                    "オーガニック"
                ]
            },
            "action_id": 115,
            "action_params": {
                "percentage": 20,
                "investment_product": "環境関連ETF",
                "destination_account": "sustainable_investment"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1021,
            "name": "🏪 コンビニ支出制限チャレンジ",
            "description": "コンビニでの1日の支出を500円以内に制限！超過分は強制的にペナルティ貯金でコンビニ依存を断ち切る節約術",
            "category": RuleCategory.REDUCE_EXPENSES,
            "author_id": 2,
            "trigger_id": 6,
            "trigger_params": {
                "category": "コンビニ",
                "operator": ">",
                "amount": 500
            },
            "action_id": 105,
            "action_params": {
                "base_amount": 500,
                "destination_account": "penalty_savings"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1022,
            "name": "📱 サブスク見直しリマインダー",
            "description": "毎月月末にサブスク支出をチェック！3,000円を超えたら不要サブスクの解約を促すアラート機能",
            "category": RuleCategory.REDUCE_EXPENSES,
            "author_id": 3,
            "trigger_id": 6,
            "trigger_params": {
                "category": "サブスクリプション",
                "operator": ">",
                "amount": 3000
            },
            "action_id": 105,
            "action_params": {
                "base_amount": 3000,
                "destination_account": "review_savings"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1023,
            "name": "🍽️ 食費月額制限システム",
            "description": "月の食費を30,000円以内に制限！予算オーバー分は自動で翌月の食費予算から天引きして計画的な食生活を実現",
            "category": RuleCategory.REDUCE_EXPENSES,
            "author_id": 1,
            "trigger_id": 6,
            "trigger_params": {
                "category": "食費",
                "operator": ">",
                "amount": 30000
            },
            "action_id": 105,
            "action_params": {
                "base_amount": 30000,
                "destination_account": "food_budget_control"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1024,
            "name": "🚇 交通費最適化ルート",
            "description": "月の交通費が15,000円を超えたら定期券や回数券の検討を促す！無駄な交通費を削減して浮いた分を自動貯金",
            "category": RuleCategory.REDUCE_EXPENSES,
            "author_id": 2,
            "trigger_id": 6,
            "trigger_params": {
                "category": "交通費",
                "operator": ">",
                "amount": 15000
            },
            "action_id": 105,
            "action_params": {
                "base_amount": 15000,
                "destination_account": "transport_savings"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1025,
            "name": "💡 光熱費削減チャレンジ",
            "description": "月の光熱費が12,000円を超えたら省エネモード発動！エアコン・照明の節約で地球にも家計にも優しい生活",
            "category": RuleCategory.REDUCE_EXPENSES,
            "author_id": 3,
            "trigger_id": 6,
            "trigger_params": {
                "category": "光熱費",
                "operator": ">",
                "amount": 12000
            },
            "action_id": 105,
            "action_params": {
                "base_amount": 12000,
                "destination_account": "utility_savings"
            },
            "is_public": True,
            "likes_count": 0,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 1026,
            "name": "🛍️ 衝動買い防止システム",
            "description": "日用品以外の支出が1日3,000円を超えたら24時間クールダウン！本当に必要かを考える時間を強制的に作る賢い仕組み",
            "category": RuleCategory.REDUCE_EXPENSES,
            "author_id": 1,
            "trigger_id": 6,
            "trigger_params": {
                "category": "雑貨・その他",
                "operator": ">",
                "amount": 3000
            },
            "action_id": 105,
            "action_params": {
                "base_amount": 3000,
                "destination_account": "impulse_control_savings"
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
        },
        {
            "id": 211,
            "name": "🎪 カフェ代節約チャレンジ",
            "description": "【カフェ通いが多い人向け・ゆるめ】コンビニ・カフェでの支出をコツコツ貯金に変換！ちょっとした節約で大きな成果を実感できるプチ贅沢系貯金術",
            "author_id": 1,
            "is_public": True,
            "likes_count": 67,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 212,
            "name": "🎯 趣味活動ミラーリング貯金",
            "description": "【趣味にお金をかけすぎる人向け・ゆるめ】推し活や趣味に使った金額と同額を自動で貯金！好きなことを楽しみながら資産も増やす両立術",
            "author_id": 2,
            "is_public": True,
            "likes_count": 134,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 213,
            "name": "🌟 ラッキーデー貯金システム",
            "description": "【運試し好き・ゆるめ】支出するたびにランダムで貯金が発動！毎日がちょっとしたワクワクに変わるギャンブル感覚の楽しい貯金術",
            "author_id": 3,
            "is_public": True,
            "likes_count": 89,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 214,
            "name": "💪 健康投資コンボシステム",
            "description": "【健康志向の人向け・ストイック】オーガニック・健康食品の購入で自動投資も発動！体への投資と資産への投資を同時に実現する一石二鳥システム",
            "author_id": 1,
            "is_public": True,
            "likes_count": 78,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 215,
            "name": "🎮 ゲーマー専用おつり貯金",
            "description": "【ゲーム課金が多い人向け・ゆるめ】ゲーム・エンタメ支出の度に自動でおつり貯金！推し活費用も確保しながらコツコツ資産形成",
            "author_id": 2,
            "is_public": True,
            "likes_count": 156,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 216,
            "name": "🍀 幸運の支出貯金",
            "description": "【日常支出が多い人向け・ゆるめ】すべての支出を「幸運の種まき」として同額貯金！支出するたびに未来への投資ができる前向き思考システム",
            "author_id": 3,
            "is_public": True,
            "likes_count": 92,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 217,
            "name": "🎨 クリエイター応援貯金",
            "description": "【推し活で罪悪感がある人向け・ゆるめ】推し活支出と同額を「クリエイター応援ファンド」として貯金！推しへの愛と将来への備えを両立",
            "author_id": 1,
            "is_public": True,
            "likes_count": 203,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 218,
            "name": "⚡ 限界突破チャレンジ",
            "description": "【浪費癖を直したい人向け・ストイック】食費の上限を設定し、オーバー分は強制ペナルティ貯金！ゲーム感覚で支出管理をマスター",
            "author_id": 2,
            "is_public": True,
            "likes_count": 45,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 219,
            "name": "🎰 デイリーガチャ貯金",
            "description": "【ガチャ・くじ引き好き向け・ゆるめ】毎日の支出でガチャが回る！ランダム貯金でドキドキワクワクしながら資産形成できる楽しいシステム",
            "author_id": 3,
            "is_public": True,
            "likes_count": 178,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 220,
            "name": "🌱 エコライフ投資術",
            "description": "【環境意識が高い人向け・ストイック】エコ・サステナブル商品の購入額に応じて環境関連投資を自動実行！地球にも財布にも優しい生活",
            "author_id": 1,
            "is_public": True,
            "likes_count": 114,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 221,
            "name": "🎪 エンタメ好き専用貯金",
            "description": "【エンタメにお金をかける人向け・ゆるめ】映画・音楽・推し活支出の度に自動貯金発動！好きなことを我慢せずに将来の備えもバッチリ",
            "author_id": 2,
            "is_public": True,
            "likes_count": 167,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 222,
            "name": "🚀 宇宙飛行士貯金計画",
            "description": "【夢追い人向け・ストイック】すべての支出を「宇宙旅行積立」として同額貯金！壮大な夢に向かって日々の支出を意味のある投資に変換",
            "author_id": 3,
            "is_public": True,
            "likes_count": 56,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 223,
            "name": "🎲 運命のサイコロ貯金",
            "description": "【運試し・ギャンブル好き向け・ゆるめ】支出のたびに確率で貯金額が決まる！運に任せて楽しみながら資産を増やすスリリングな貯金術",
            "author_id": 1,
            "is_public": True,
            "likes_count": 129,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 224,
            "name": "💎 推しと共に成長ファンド",
            "description": "【推し活と資産形成を両立したい人向け・ゆるめ】推し活支出と同額を長期投資ファンドへ！推しと一緒に資産も成長する究極の両立システム",
            "author_id": 2,
            "is_public": True,
            "likes_count": 234,
            "copies_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 225,
            "name": "⭐ 奇跡の支出変換術",
            "description": "【支出を資産に変えたい人向け・ストイック】全支出をEXPとして蓄積し、一定額に達したら自動投資発動！RPG感覚で楽しく資産形成",
            "author_id": 3,
            "is_public": True,
            "likes_count": 87,
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
            "rule_template_id": 1008
        },
        {
            "recipe_template_id": 201,
            "rule_template_id": 1004
        },
        {
            "recipe_template_id": 201,
            "rule_template_id": 1021
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
            "recipe_template_id": 202,
            "rule_template_id": 1022
        },
        {
            "recipe_template_id": 203,
            "rule_template_id": 1005
        },
        {
            "recipe_template_id": 203,
            "rule_template_id": 1006
        },
        {
            "recipe_template_id": 203,
            "rule_template_id": 1020
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
        {
            "recipe_template_id": 204,
            "rule_template_id": 1024
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
        {
            "recipe_template_id": 205,
            "rule_template_id": 1025
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
            "rule_template_id": 1005
        },
        {
            "recipe_template_id": 207,
            "rule_template_id": 1006
        },
        {
            "recipe_template_id": 207,
            "rule_template_id": 1020
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
        {
            "recipe_template_id": 208,
            "rule_template_id": 1019
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
        {
            "recipe_template_id": 209,
            "rule_template_id": 1004
        },
        # ⚡ 推し活断捨離チャレンジ
        {
            "recipe_template_id": 210,
            "rule_template_id": 1009
        },
        {
            "recipe_template_id": 210,
            "rule_template_id": 1017
        },
        {
            "recipe_template_id": 210,
            "rule_template_id": 1019
        },
        # 🎪 カフェ代節約チャレンジ
        {
            "recipe_template_id": 211,
            "rule_template_id": 1021
        },
        {
            "recipe_template_id": 211,
            "rule_template_id": 1004
        },
        {
            "recipe_template_id": 211,
            "rule_template_id": 1013
        },
        # 🎯 趣味活動ミラーリング貯金
        {
            "recipe_template_id": 212,
            "rule_template_id": 1014
        },
        {
            "recipe_template_id": 212,
            "rule_template_id": 1021
        },
        # 🌟 ラッキーデー貯金システム
        {
            "recipe_template_id": 213,
            "rule_template_id": 1009
        },
        {
            "recipe_template_id": 213,
            "rule_template_id": 1022
        },
        # 💪 健康投資コンボシステム
        {
            "recipe_template_id": 214,
            "rule_template_id": 1023
        },
        {
            "recipe_template_id": 214,
            "rule_template_id": 1005
        },
        {
            "recipe_template_id": 214,
            "rule_template_id": 1020
        },
        # 🎮 ゲーマー専用おつり貯金
        {
            "recipe_template_id": 215,
            "rule_template_id": 1022
        },
        {
            "recipe_template_id": 215,
            "rule_template_id": 1005
        },
        {
            "recipe_template_id": 215,
            "rule_template_id": 1013
        },
        # 🍀 幸運の支出貯金
        {
            "recipe_template_id": 216,
            "rule_template_id": 1010
        },
        {
            "recipe_template_id": 216,
            "rule_template_id": 1023
        },
        # 🎨 クリエイター応援貯金
        {
            "recipe_template_id": 217,
            "rule_template_id": 1014
        },
        {
            "recipe_template_id": 217,
            "rule_template_id": 1024
        },
        # ⚡ 限界突破チャレンジ
        {
            "recipe_template_id": 218,
            "rule_template_id": 1024
        },
        {
            "recipe_template_id": 218,
            "rule_template_id": 1007
        },
        {
            "recipe_template_id": 218,
            "rule_template_id": 1013
        },
        # 🎰 デイリーガチャ貯金
        {
            "recipe_template_id": 219,
            "rule_template_id": 1009
        },
        {
            "recipe_template_id": 219,
            "rule_template_id": 1025
        },
        # 🌱 エコライフ投資術
        {
            "recipe_template_id": 220,
            "rule_template_id": 1025
        },
        {
            "recipe_template_id": 220,
            "rule_template_id": 1005
        },
        {
            "recipe_template_id": 220,
            "rule_template_id": 1020
        },
        # 🎪 エンタメ好き専用貯金
        {
            "recipe_template_id": 221,
            "rule_template_id": 1026
        },
        {
            "recipe_template_id": 221,
            "rule_template_id": 1005
        },
        {
            "recipe_template_id": 221,
            "rule_template_id": 1013
        },
        # 🚀 宇宙飛行士貯金計画
        {
            "recipe_template_id": 222,
            "rule_template_id": 1010
        },
        {
            "recipe_template_id": 222,
            "rule_template_id": 1026
        },
        # 🎲 運命のサイコロ貯金
        {
            "recipe_template_id": 223,
            "rule_template_id": 1009
        },
        {
            "recipe_template_id": 223,
            "rule_template_id": 1026
        },
        # 💎 推しと共に成長ファンド
        {
            "recipe_template_id": 224,
            "rule_template_id": 1014
        },
        {
            "recipe_template_id": 224,
            "rule_template_id": 1025
        },
        # ⭐ 奇跡の支出変換術
        {
            "recipe_template_id": 225,
            "rule_template_id": 1011
        },
        {
            "recipe_template_id": 225,
            "rule_template_id": 1026
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
        },
        # ユーザー4（みらしー）のプリファレンス
        {
            "user_id": 4,
            "question": "あなたの推しはなにブヒ？",
            "selected_answers": "アニメ;ゲーム"
        },
        {
            "user_id": 4,
            "question": "推し活の内容はなにブヒ？",
            "selected_answers": "グッズ購入;イベント参加"
        },
        {
            "user_id": 4,
            "question": "今や将来の生活のための備えができているブヒか？",
            "selected_answers": "学生だからお金のことはまだよくわからないブヒ"
        },
        {
            "user_id": 4,
            "question": "月に自由に使えるお金はいくらくらいブヒ？",
            "selected_answers": "1,000円〜4,999円"
        },
        {
            "user_id": 4,
            "question": "お金の目標を設定するブヒ",
            "selected_answers": "推し活をもっと楽しみたいブヒ"
        },
        {
            "user_id": 4,
            "question": "家族構成を教えてブヒ",
            "selected_answers": "実家暮らし"
        },
        {
            "user_id": 4,
            "question": "今支払いに使っているカードと銀行を教えてブヒ",
            "selected_answers": "学生カード;ゆうちょ銀行"
        },
        # ユーザー5（おしあい）のプリファレンス
        {
            "user_id": 5,
            "question": "あなたの推しはなにブヒ？",
            "selected_answers": "アイドル;インフルエンサー"
        },
        {
            "user_id": 5,
            "question": "推し活の内容はなにブヒ？",
            "selected_answers": "サブスク利用;グッズ購入;投げ銭"
        },
        {
            "user_id": 5,
            "question": "今や将来の生活のための備えができているブヒか？",
            "selected_answers": "ある程度は貯金してるし、将来も安心ブヒ"
        },
        {
            "user_id": 5,
            "question": "月に自由に使えるお金はいくらくらいブヒ？",
            "selected_answers": "30,000円〜49,999円"
        },
        {
            "user_id": 5,
            "question": "お金の目標を設定するブヒ",
            "selected_answers": "マイホームを購入したいブヒ"
        },
        {
            "user_id": 5,
            "question": "家族構成を教えてブヒ",
            "selected_answers": "一人暮らし"
        },
        {
            "user_id": 5,
            "question": "今支払いに使っているカードと銀行を教えてブヒ",
            "selected_answers": "楽天カード;楽天銀行"
        },
        # ユーザー6（がちゃらき）のプリファレンス
        {
            "user_id": 6,
            "question": "あなたの推しはなにブヒ？",
            "selected_answers": "ゲーム;アニメ;YouTuber"
        },
        {
            "user_id": 6,
            "question": "推し活の内容はなにブヒ？",
            "selected_answers": "課金;グッズ購入"
        },
        {
            "user_id": 6,
            "question": "今や将来の生活のための備えができているブヒか？",
            "selected_answers": "貯金もあんまりないしちょっと不安ブヒ"
        },
        {
            "user_id": 6,
            "question": "月に自由に使えるお金はいくらくらいブヒ？",
            "selected_answers": "10,000円〜19,999円"
        },
        {
            "user_id": 6,
            "question": "お金の目標を設定するブヒ",
            "selected_answers": "推し活をもっと楽しみたいブヒ"
        },
        {
            "user_id": 6,
            "question": "家族構成を教えてブヒ",
            "selected_answers": "実家暮らし"
        },
        {
            "user_id": 6,
            "question": "今支払いに使っているカードと銀行を教えてブヒ",
            "selected_answers": "PayPayカード;PayPay銀行"
        },
        # ユーザー7（せつやく王）のプリファレンス
        {
            "user_id": 7,
            "question": "あなたの推しはなにブヒ？",
            "selected_answers": "アーティスト;読書"
        },
        {
            "user_id": 7,
            "question": "推し活の内容はなにブヒ？",
            "selected_answers": "サブスク利用;イベント参加"
        },
        {
            "user_id": 7,
            "question": "今や将来の生活のための備えができているブヒか？",
            "selected_answers": "ある程度は貯金してるし、将来も安心ブヒ"
        },
        {
            "user_id": 7,
            "question": "月に自由に使えるお金はいくらくらいブヒ？",
            "selected_answers": "20,000円〜29,999円"
        },
        {
            "user_id": 7,
            "question": "お金の目標を設定するブヒ",
            "selected_answers": "老後の生活資金を準備したいブヒ"
        },
        {
            "user_id": 7,
            "question": "家族構成を教えてブヒ",
            "selected_answers": "夫婦"
        },
        {
            "user_id": 7,
            "question": "今支払いに使っているカードと銀行を教えてブヒ",
            "selected_answers": "イオンカード;みずほ銀行"
        },
        # ユーザー8（未来投資家）のプリファレンス
        {
            "user_id": 8,
            "question": "あなたの推しはなにブヒ？",
            "selected_answers": "アーティスト;映画"
        },
        {
            "user_id": 8,
            "question": "推し活の内容はなにブヒ？",
            "selected_answers": "イベント参加;サブスク利用"
        },
        {
            "user_id": 8,
            "question": "今や将来の生活のための備えができているブヒか？",
            "selected_answers": "投資もしてるし、将来はバッチリブヒ！"
        },
        {
            "user_id": 8,
            "question": "月に自由に使えるお金はいくらくらいブヒ？",
            "selected_answers": "50,000円以上"
        },
        {
            "user_id": 8,
            "question": "お金の目標を設定するブヒ",
            "selected_answers": "投資で資産を増やしたいブヒ"
        },
        {
            "user_id": 8,
            "question": "家族構成を教えてブヒ",
            "selected_answers": "一人暮らし"
        },
        {
            "user_id": 8,
            "question": "今支払いに使っているカードと銀行を教えてブヒ",
            "selected_answers": "アメリカンエキスプレス;三井住友銀行"
        },
        # ユーザー9（はなコツ）のプリファレンス
        {
            "user_id": 9,
            "question": "あなたの推しはなにブヒ？",
            "selected_answers": "アイドル;アニメ"
        },
        {
            "user_id": 9,
            "question": "推し活の内容はなにブヒ？",
            "selected_answers": "グッズ購入;サブスク利用"
        },
        {
            "user_id": 9,
            "question": "今や将来の生活のための備えができているブヒか？",
            "selected_answers": "貯金もあんまりないしちょっと不安ブヒ"
        },
        {
            "user_id": 9,
            "question": "月に自由に使えるお金はいくらくらいブヒ？",
            "selected_answers": "10,000円〜19,999円"
        },
        {
            "user_id": 9,
            "question": "お金の目標を設定するブヒ",
            "selected_answers": "結婚や出産、子育てのためにお金を貯めたいブヒ"
        },
        {
            "user_id": 9,
            "question": "家族構成を教えてブヒ",
            "selected_answers": "一人暮らし"
        },
        {
            "user_id": 9,
            "question": "今支払いに使っているカードと銀行を教えてブヒ",
            "selected_answers": "dカード;三菱UFJ銀行"
        },
        # ユーザー10（りじゅ）のプリファレンス
        {
            "user_id": 10,
            "question": "あなたの推しはなにブヒ？",
            "selected_answers": "読書;映画;美容"
        },
        {
            "user_id": 10,
            "question": "推し活の内容はなにブヒ？",
            "selected_answers": "サブスク利用;グッズ購入"
        },
        {
            "user_id": 10,
            "question": "今や将来の生活のための備えができているブヒか？",
            "selected_answers": "ある程度は貯金してるし、将来も安心ブヒ"
        },
        {
            "user_id": 10,
            "question": "月に自由に使えるお金はいくらくらいブヒ？",
            "selected_answers": "30,000円〜49,999円"
        },
        {
            "user_id": 10,
            "question": "お金の目標を設定するブヒ",
            "selected_answers": "自分の趣味やライフスタイルを充実させたいブヒ"
        },
        {
            "user_id": 10,
            "question": "家族構成を教えてブヒ",
            "selected_answers": "夫婦"
        },
        {
            "user_id": 10,
            "question": "今支払いに使っているカードと銀行を教えてブヒ",
            "selected_answers": "JCBカード;りそな銀行"
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

# ===== サンプルユーザーレシピ（ユーザーが選択したレシピ）関連 =====

def seed_sample_user_recipes(session_maker=None):
    if session_maker is None:
        session_maker = SessionLocal
    
    db = session_maker()
    try:
        create_sample_user_recipes(db)
        db.commit()
    except Exception as e:
        print(f"サンプルユーザーレシピデータ投入エラー: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_sample_user_recipes(db: Session):
    from models import Recipe
    current_time = datetime.now(timezone.utc)
    
    user_recipes_data = [
        {
            "id": 1,
            "name": "ヒヨコ貯金チャレンジ",
            "description": "【推し活初心者向け・ゆるめ】推しにお金を使いすぎて貯金ゼロの人でも大丈夫！小額からコツコツ始められる可愛い貯金術",
            "template_id": 202,
            "user_id": 2,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 2,
            "name": "🎰 ガチャ貯金システム 🎰",
            "description": "【推し活ガチャ好き向け・ゆるめ】課金感覚で楽しく貯金！支出するたびにランダム貯金で運試し。推しのガチャ資金も貯まる一石二鳥システム",
            "template_id": 204,
            "user_id": 4,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 3,
            "name": "🌸 推しと共に成長する資産形成 💎",
            "description": "【推し活で罪悪感がある人向け・ゆるめ】推しへの愛と同じ分だけ自分にも投資！推し活を諦めずに資産も増やす究極の両立術",
            "template_id": 208,
            "user_id": 5,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 4,
            "name": "🎰 ガチャ貯金システム 🎰",
            "description": "【推し活ガチャ好き向け・ゆるめ】課金感覚で楽しく貯金！支出するたびにランダム貯金で運試し。推しのガチャ資金も貯まる一石二鳥システム",
            "template_id": 204,
            "user_id": 6,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 5,
            "name": "WHY 浪費 PEOPLE ! ? 🔥",
            "description": "【推し活ガチ勢向け・ストイック】推しへの愛は変えずに無駄遣いを徹底カット！本気で資産形成したい推し活民のための鬼レシピ",
            "template_id": 203,
            "user_id": 7,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 6,
            "name": "⏰ タイムトラベラー投資術 ⏰",
            "description": "【推し活で将来不安な人向け・ストイック】過去・現在・未来の3つの時間軸で資産管理。SF好きな推し活民が楽しく長期投資できる仕組み",
            "template_id": 207,
            "user_id": 8,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 7,
            "name": "ヒヨコ貯金チャレンジ",
            "description": "【推し活初心者向け・ゆるめ】推しにお金を使いすぎて貯金ゼロの人でも大丈夫！小額からコツコツ始められる可愛い貯金術",
            "template_id": 202,
            "user_id": 9,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "id": 8,
            "name": "🌸 推しと共に成長する資産形成 💎",
            "description": "【推し活で罪悪感がある人向け・ゆるめ】推しへの愛と同じ分だけ自分にも投資！推し活を諦めずに資産も増やす究極の両立術",
            "template_id": 208,
            "user_id": 10,
            "created_at": current_time,
            "updated_at": current_time
        }
    ]
    
    for recipe_data in user_recipes_data:
        # 既存データをチェック
        existing = db.query(Recipe).filter(Recipe.id == recipe_data["id"]).first()
        if not existing:
            recipe = Recipe(**recipe_data)
            db.add(recipe)
    
    print(f"サンプルユーザーレシピ {len(user_recipes_data)} 件投入完了")