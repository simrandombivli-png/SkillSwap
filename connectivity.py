from datetime import datetime
from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, Float, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

app = FastAPI(
    title="SkillSwap API",
    description="Peer-to-Peer Student Time Bank with MySQL Integration",
    version="1.0",
)

# ============================================================
# 1. MYSQL DATABASE CONNECTIVITY
# ============================================================
DATABASE_URL = "mysql+pymysql://root:1025147@localhost:3306/skillswap_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================
# 2. SQL ALCHEMY MODELS (Automatically creates tables in MySQL)
# ============================================================
class UserModel(Base):
  __tablename__ = "users"
  id = Column(Integer, primary_key=True, index=True, autoincrement=True)
  name = Column(String(100), nullable=False)
  email = Column(String(100), unique=True, index=True, nullable=False)
  department = Column(String(100), nullable=False)
  availability = Column(Text, default="")
  credits = Column(Integer, default=5)
  rating = Column(Float, default=0.0)
  rating_count = Column(Integer, default=0)


# Automatically builds tables in MySQL when the application boots up
Base.metadata.create_all(bind=engine)


def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()


# ============================================================
# 3. REQUEST MODELS (Pydantic)
# ============================================================
class UserCreate(BaseModel):
  name: str
  email: str
  department: str
  availability: List[str] = []


# ============================================================
# 4. HOME & USER ENDPOINTS
# ============================================================
@app.get("/")
def home():
  return {
      "message": "SkillSwap API is running with MySQL Database",
      "status": "success",
  }


@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
  # Check if email already exists in MySQL
  existing_user = (
      db.query(UserModel).filter(UserModel.email == user.email).first()
  )
  if existing_user:
    raise HTTPException(status_code=400, detail="Email already registered")

  # Create a new user record for MySQL
  new_user = UserModel(
      name=user.name,
      email=user.email,
      department=user.department,
      availability=",".join(user.availability),
      credits=5,
      rating=0.0,
      rating_count=0,
  )

  db.add(new_user)
  db.commit()
  db.refresh(new_user)

  return {
      "message": "User registered successfully in MySQL!",
      "user": {
          "id": new_user.id,
          "name": new_user.name,
          "email": new_user.email,
          "department": new_user.department,
          "credits": new_user.credits,
      },
  }


@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
  user = db.query(UserModel).filter(UserModel.id == user_id).first()
  if not user:
    raise HTTPException(status_code=404, detail="User not found")
  return {
      "id": user.id,
      "name": user.name,
      "email": user.email,
      "department": user.department,
      "credits": user.credits,
      "rating": user.rating,
  }
