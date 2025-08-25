from pydantic import BaseModel, EmailStr, validator, Field
from datetime import date, datetime
from typing import List, Any, Optional
from enums import RuleCategory
from pydantic import conint


class UserRegister(BaseModel):
    last_name: str
    first_name: str
    email: EmailStr
    birthdate: date
    occupation: str
    company_name: str
    password: str
    password_confirm: str

    @validator('last_name', 'first_name', 'occupation', 'company_name')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('This field cannot be empty')
        return v.strip()

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @validator('password_confirm')
    def validate_password_confirm(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Password confirmation does not match')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    last_name: str
    first_name: str
    email: str
    birthdate: date
    occupation: str
    company_name: str
    nickname: Optional[str] = None

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    message: str

class Preference(BaseModel):
    id: int = Field(..., description="ID")
    user_id: int = Field(..., description="ユーザーID")
    question: str = Field(..., description="質問の内容", example="好きな色は何ですか？")
    selected_answers: List[str] = Field(..., description="選択された回答のリスト（複数選択可能）", example=["赤", "青"])

class PreferenceCreate(BaseModel):
    user_id: int = Field(..., description="ユーザーID", gt=0)
    question: str = Field(..., description="質問の内容", min_length=1, example="好きな色は何ですか？")
    selected_answers: List[str] = Field(..., description="選択された回答のリスト（複数選択可能）", min_items=1, example=["赤", "青"])

    @validator('user_id')
    def validate_user_id(cls, v):
        if v <= 0:
            raise ValueError('ユーザーIDは1以上の値を指定してください')
        return v

    @validator('question')
    def validate_question(cls, v):
        if not v or not v.strip():
            raise ValueError('質問内容を入力してください')
        return v.strip()

    @validator('selected_answers')
    def validate_selected_answers(cls, v):
        if not v:
            raise ValueError('回答を1つ以上選択してください')
        return v


class Trigger(BaseModel):
    id: int = Field(..., description="ID")
    name: str = Field(..., description="トリガーの名前")
    description: str = Field(..., description="トリガーの説明")
    required_params: Any = Field(..., description="必要なパラメータ")

    class Config:
        from_attributes = True

class Action(BaseModel):
    id: int = Field(..., description="ID")
    name: str = Field(..., description="アクションの名前")
    description: str = Field(..., description="アクションの説明")
    required_params: Any = Field(..., description="必要なパラメータ")

    class Config:
        from_attributes = True

class RuleTemplateWithTriggerAndAction(BaseModel):
    id: int = Field(..., description="ID")
    name: str = Field(..., description="ルールテンプレートの名前")
    description: str = Field(..., description="ルールテンプレートの説明")
    category: RuleCategory = Field(..., description="ルールテンプレートのカテゴリ")
    author_id: int = Field(..., description="作成者のユーザーID")
    is_public: bool = Field(..., description="公開設定")
    likes_count: int = Field(..., description="いいね数")
    copies_count: int = Field(..., description="コピー数")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    trigger: Trigger = Field(..., description="トリガー")
    trigger_params: Any = Field(..., description="トリガーのパラメータ")  
    action: Action = Field(..., description="アクション")
    action_params: Any = Field(..., description="アクションのパラメータ")

    class Config:
        from_attributes = True

class RecipeTemplateWithUserAndRuleTemplatesWithTriggerAndAction(BaseModel):
    id: int = Field(..., description="ID")
    name: str = Field(..., description="レシピテンプレートの名前")
    description: str = Field(..., description="レシピテンプレートの説明")
    author_id: int = Field(..., description="作成者のユーザーID")
    is_public: bool = Field(..., description="公開設定")
    likes_count: int = Field(..., description="いいね数")
    copies_count: int = Field(..., description="コピー数")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    user: UserResponse = Field(..., description="ユーザー")
    rules: List[RuleTemplateWithTriggerAndAction] = Field(..., description="ルールテンプレートのリスト")

    class Config:
        from_attributes = True

class RuleWithTriggerAndAction(BaseModel):
    id: int = Field(..., description="ID")
    name: str = Field(..., description="ルールの名前")
    description: str = Field(..., description="ルールの説明")
    category: RuleCategory = Field(..., description="ルールのカテゴリ")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    trigger: Trigger = Field(..., description="トリガー")
    trigger_params: Any = Field(..., description="トリガーのパラメータ")
    action: Action = Field(..., description="アクション")
    action_params: Any = Field(..., description="アクションのパラメータ")

    class Config:
        from_attributes = True

class RecipeWithUserAndRulesWithTriggerAndAction(BaseModel):
    id: int = Field(..., description="ID")
    name: str = Field(..., description="レシピの名前")
    description: str = Field(..., description="レシピの説明")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    user: UserResponse = Field(..., description="ユーザー")
    rules: List[RuleWithTriggerAndAction] = Field(..., description="ルールのリスト")

    class Config:
        from_attributes = True


class RecipeCreate(BaseModel):
    user_id: int = Field(..., description="ユーザーID")
    template_id: int = Field(..., description="レシピテンプレートID")

class CategorySummary(BaseModel):
    category: str = Field(..., description="支出のカテゴリ")
    total_amount: int = Field(..., description="支出の合計金額")

class FinancialReport(BaseModel):
    date: str = Field(..., description="日付")
    user_id: int = Field(..., description="ユーザーID")
    insights: List[str] = Field(..., description="インサイトのリスト")
    expenses_by_category: List[CategorySummary] = Field(..., description="支出のカテゴリごとの合計金額")
    income_total: int = Field(..., description="選択した銀行からの収入合計")
    expense_total: int = Field(..., description="選択したカードからの支出合計（絶対値）")
    balance_total: int = Field(..., description="収支（収入 - 支出）")

class UserNicknameSet(BaseModel):
    user_id: int = Field(..., description="ユーザーID", gt=0)
    nickname: str = Field(..., description="ニックネーム", min_length=1, max_length=10)

    @validator('user_id')
    def validate_user_id(cls, v):
        if v <= 0:
            raise ValueError('ユーザーIDは1以上の値を指定してください')
        return v

    @validator('nickname')
    def validate_nickname(cls, v):
        if not v or not v.strip():
            raise ValueError('ニックネームを入力してください')
        if len(v.strip()) > 10:
            raise ValueError('ニックネームは10文字以内で入力してください')
        return v.strip()

class TanabotaExecuteRequest(BaseModel):
    user_id: int = Field(..., ge=1)
    amount: conint(ge=0, le=999_999_999_999)  # 円（整数）

class TanabotaExecutionItem(BaseModel):
    rule_id: int
    action_id: int
    action_type: str
    tanabota_amount: int  # 円（整数）

class TanabotaExecuteResponse(BaseModel):
    transaction_id: int
    amount_paid: int
    tanabota_total: int
    executions: List[TanabotaExecutionItem]

class TanabotaTxSummary(BaseModel):
    id: int
    user_id: int
    amount_paid: int
    tanabota_total: int

class TanabotaTxDetail(TanabotaTxSummary):
    executions: List[TanabotaExecutionItem] = []
