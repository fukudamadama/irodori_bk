from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from models import get_db, User, hash_password, verify_password
from schemas import UserRegister, UserLogin, UserResponse, MessageResponse

router = APIRouter(tags=["auth"])

@router.post("/register", response_model=MessageResponse)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(user_data.password)
    
    new_user = User(
        last_name=user_data.last_name,
        first_name=user_data.first_name,
        email=user_data.email,
        birth_date=user_data.birth_date,
        postal_code=user_data.postal_code,
        address=user_data.address,
        phone_number=user_data.phone_number,
        occupation=user_data.occupation,
        company_name=user_data.company_name,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return MessageResponse(message="User registered successfully")

@router.post("/login", response_model=MessageResponse)
def login_user(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    request.session["user_id"] = user.id
    return MessageResponse(message="Login successful")

@router.get("/logout", response_model=MessageResponse)
def logout_user(request: Request):
    if "user_id" not in request.session:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    request.session.clear()
    return MessageResponse(message="Logout successful")

@router.get("/me", response_model=UserResponse)
def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse.from_orm(user)