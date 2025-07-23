from pydantic import BaseModel, EmailStr, validator
from datetime import date
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