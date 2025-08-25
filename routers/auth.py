from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import hash_password, verify_password
from schemas import UserRegister, UserLogin, UserResponse, MessageResponse

router = APIRouter(tags=["auth"])

@router.post("/register", response_model=UserResponse)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(user_data.password)
    
    new_user = User(
        last_name=user_data.last_name,
        first_name=user_data.first_name,
        email=user_data.email,
        birthdate=user_data.birthdate,
        postal_code="",
        address="",
        phone_number="",
        occupation=user_data.occupation,
        company_name=user_data.company_name,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        id=new_user.id,
        last_name=new_user.last_name,
        first_name=new_user.first_name,
        email=new_user.email,
        birthdate=new_user.birthdate,
        occupation=new_user.occupation,
        company_name=new_user.company_name,
        nickname=new_user.nickname
    )

@router.post("/login", response_model=UserResponse)
def login_user(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    request.session["user_id"] = user.id
    return UserResponse(
        id=user.id,
        last_name=user.last_name,
        first_name=user.first_name,
        email=user.email,
        birthdate=user.birthdate,
        occupation=user.occupation,
        company_name=user.company_name,
        nickname=user.nickname
    )

@router.get("/logout", response_model=MessageResponse)
def logout_user(request: Request):
    # セッションをクリア（ログイン状態に関係なく）
    request.session.clear()
    return MessageResponse(message="Logout successful")

