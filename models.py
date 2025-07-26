from sqlalchemy import Column, Integer, String, Date, DateTime
from datetime import datetime, timezone
from database import Base, engine

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

Base.metadata.create_all(bind=engine)