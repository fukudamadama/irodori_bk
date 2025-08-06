from datetime import date, datetime, timezone
from database import SessionLocal
from models import User, Preference
from auth import hash_password

def insert_test_data():
    db = SessionLocal()
    try:
        # テストユーザー1の作成
        test_user1 = User(
            last_name="山田",
            first_name="太郎",
            email="yamada@example.com",
            birthdate=date(1990, 1, 15),
            postal_code="123-4567",
            address="東京都渋谷区渋谷1-1-1",
            phone_number="090-1234-5678",
            occupation="会社員",
            company_name="株式会社テスト",
            password_hash=hash_password("test123")
        )
        db.add(test_user1)
        db.flush()  # IDを取得するためにflush

        # テストユーザー1の好みデータ
        test_preference1 = Preference(
            user_id=test_user1.id,
            question="好きな色は何ですか？",
            selected_answers="赤;青;緑"
        )
        test_preference2 = Preference(
            user_id=test_user1.id,
            question="趣味は何ですか？",
            selected_answers="読書;映画鑑賞;旅行"
        )
        db.add(test_preference1)
        db.add(test_preference2)

        # テストユーザー2の作成
        test_user2 = User(
            last_name="佐藤",
            first_name="花子",
            email="sato@example.com",
            birthdate=date(1995, 5, 20),
            postal_code="234-5678",
            address="東京都新宿区新宿2-2-2",
            phone_number="090-8765-4321",
            occupation="デザイナー",
            company_name="デザイン株式会社",
            password_hash=hash_password("test456")
        )
        db.add(test_user2)
        db.flush()

        # テストユーザー2の好みデータ
        test_preference3 = Preference(
            user_id=test_user2.id,
            question="好きな食べ物は何ですか？",
            selected_answers="寿司;ラーメン;カレー"
        )
        test_preference4 = Preference(
            user_id=test_user2.id,
            question="休日の過ごし方は？",
            selected_answers="スポーツ;ショッピング;カフェ巡り"
        )
        db.add(test_preference3)
        db.add(test_preference4)

        db.commit()
        print("テストデータの挿入が完了しました。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    insert_test_data()