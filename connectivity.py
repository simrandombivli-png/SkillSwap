import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "skillswap_db")

# Construct the SQLAlchemy database connection URL using PyMySQL driver[span_3](start_span)[span_3](end_span)
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Initialize the database engine and session factory
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency injector used across FastAPI endpoints to open and safely close sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================================================================
# SQLALCHEMY DATABASE MODELS (Mapping to MySQL Tables)
# =====================================================================

class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    department = Column(String(100))
    availability = Column(Text)
    credits = Column(Integer, default=5)
    rating = Column(Float, default=0.0)


class SkillModel(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    skill_name = Column(String(100), nullable=False)
    skill_type = Column(String(50), nullable=False)


class BookingModel(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, nullable=False)
    tutor_id = Column(Integer, nullable=False)
    skill_id = Column(Integer, nullable=False)
    date = Column(String(50), nullable=False)
    start_time = Column(String(50), nullable=False)
    duration = Column(Integer, nullable=False)
    credits = Column(Integer, nullable=False)
    status = Column(String(50), default="pending")


class TransactionModel(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    type = Column(String(50), nullable=False)
    amount = Column(Integer, nullable=False)
    booking_id = Column(Integer)
