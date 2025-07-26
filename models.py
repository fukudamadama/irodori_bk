from sqlalchemy import Column, Integer, String, Date, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import bcrypt
import os

# 環境変数の読み込み
from dotenv import load_dotenv
load_dotenv()

# Azure MySQL 接続設定
def get_database_url():
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_ssl_ca = os.getenv("DB_SSL_CA")
    db_ssl_mode = os.getenv("DB_SSL_MODE", "REQUIRED")
    
    print(f"DB Config - Host: {db_host}, DB: {db_name}, User: {db_user}")
    
    if all([db_host, db_name, db_user, db_password]):
        # Azure MySQL with SSL
        url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?ssl_ca={db_ssl_ca}&ssl_verify_cert=true&ssl_verify_identity=true"
        print(f"Using Azure MySQL: {db_host}")
        return url
    else:
        # Fallback to SQLite
        print("Falling back to SQLite")
        return "sqlite:///./app.db"

SQLALCHEMY_DATABASE_URL = get_database_url()

if SQLALCHEMY_DATABASE_URL.startswith("mysql"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
else:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    birthdate = Column(Date, nullable=False)
    postal_code = Column(String(10), nullable=False)
    address = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    occupation = Column(String(100), nullable=False)
    company_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

Base.metadata.create_all(bind=engine)