from pydantic import BaseModel, EmailStr, validator, Field
from datetime import date
from typing import List
import re

class UserRegister(BaseModel):
    last_name: str
    first_name: str
    email: EmailStr
    birthdate: date
    postal_code: str
    address: str
    phone_number: str
    occupation: str
    company_name: str
    password: str
    password_confirm: str

    @validator('last_name', 'first_name', 'address', 'occupation', 'company_name')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('This field cannot be empty')
        return v.strip()

    @validator('postal_code')
    def validate_postal_code(cls, v):
        if not re.match(r'^\d{3}-\d{4}$', v):
            raise ValueError('Postal code must be in format 123-4567')
        return v

    @validator('phone_number')
    def validate_phone_number(cls, v):
        digits_only = re.sub(r'\D', '', v)
        if len(digits_only) < 10 or len(digits_only) > 11:
            raise ValueError('Phone number must be 10-11 digits')
        return digits_only

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
    postal_code: str
    address: str
    phone_number: str
    occupation: str
    company_name: str

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