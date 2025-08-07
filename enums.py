import enum

# ルールのカテゴリを定義するEnum
class RuleCategory(enum.Enum):
    INCREASE_SAVINGS = "貯金"
    ASSET_MANAGEMENT = "投資"
    REDUCE_EXPENSES = "節約"