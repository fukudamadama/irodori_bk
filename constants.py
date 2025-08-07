"""
アプリケーション全体で使用される定数を定義
"""

# 質問関連の定数
FINANCIAL_PROVIDER_QUESTION = "今支払いに使っているカードと銀行を教えてブヒ"

# デモ用金融データ
DEMO_FINANCIAL_PROVIDERS = [
    # 銀行データ（収入）- 高水準
    {
        "name": "三友銀行",
        "transactions": [
            {"amount": 400000, "category": "給与"},
            {"amount": 100000, "category": "副業収入"}
        ]
    },
    # 銀行データ（収入）- 中水準  
    {
        "name": "みずほ銀行",
        "transactions": [
            {"amount": 300000, "category": "給与"},
            {"amount": 50000, "category": "副業収入"}
        ]
    },
    # 銀行データ（収入）- 低水準
    {
        "name": "楽天銀行",
        "transactions": [
            {"amount": 250000, "category": "給与"}
        ]
    },
    # カードデータ（支出）- 高水準
    {
        "name": "三友カード",
        "transactions": [
            {"amount": -150000, "category": "生活費"},
            {"amount": -80000, "category": "推し活"},
            {"amount": -100000, "category": "貯金"},
            {"amount": -50000, "category": "投資"}
        ]
    },
    # カードデータ（支出）- 中水準
    {
        "name": "サゾンカード",
        "transactions": [
            {"amount": -100000, "category": "生活費"},
            {"amount": -50000, "category": "推し活"},
            {"amount": -60000, "category": "貯金"},
            {"amount": -30000, "category": "投資"}
        ]
    },
    # カードデータ（支出）- 低水準
    {
        "name": "楽天カード",
        "transactions": [
            {"amount": -80000, "category": "生活費"},
            {"amount": -25000, "category": "推し活"},
            {"amount": -40000, "category": "貯金"},
            {"amount": -15000, "category": "投資"}
        ]
    }
]