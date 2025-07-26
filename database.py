from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

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
        url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?ssl_ca={db_ssl_ca}&ssl_verify_cert=true&ssl_verify_identity=true"
        print(f"Using Azure MySQL: {db_host}")
        return url
    else:
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()