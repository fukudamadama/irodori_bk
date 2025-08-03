"""
アプリケーション全体で使用される定数を定義
"""

# 質問関連の定数
FINANCIAL_PROVIDER_QUESTION = "今支払いに使っているカードと銀行を教えてブヒ"

# デモ用金融データ
DEMO_FINANCIAL_PROVIDERS = [
    {
        "name": "三友カード",
        "transactions": [
            {"amount": -80000, "category": "生活費"},
            {"amount": -50000, "category": "推し活"},
            {"amount": -30000, "category": "変動費"}
        ]
    },
    {
        "name": "三友銀行", 
        "transactions": [
            {"amount": -120000, "category": "生活費"},
            {"amount": -40000, "category": "推し活"},
            {"amount": -25000, "category": "変動費"}
        ]
    },
    {
        "name": "楽天カード",
        "transactions": [
            {"amount": -60000, "category": "生活費"},
            {"amount": -35000, "category": "推し活"},
            {"amount": -20000, "category": "変動費"}
        ]
    }
]