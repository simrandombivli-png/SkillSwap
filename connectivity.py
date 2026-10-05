from sqlalchemy import Column, Float, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# MySQL Database URL
DATABASE_URL = "mysql+pymysql://root:1025147@localhost:3306/skillswap_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models (Tables)
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


class SkillModel(Base):
  __tablename__ = "skills"
  id = Column(Integer, primary_key=True, index=True, autoincrement=True)
  user_id = Column(Integer, nullable=False)
  skill_name = Column(String(100), nullable=False)
  skill_type = Column(String(50), nullable=False)


class BookingModel(Base):
  __tablename__ = "bookings"
  id = Column(Integer, primary_key=True, index=True, autoincrement=True)
  student_id = Column(Integer, nullable=False)
  tutor_id = Column(Integer, nullable=False)
  skill_id = Column(Integer, nullable=False)
  date = Column(String(50), nullable=False)
  start_time = Column(String(50), nullable=False)
  duration = Column(Integer, nullable=False)
  credits = Column(Integer, nullable=False)
  status = Column(String(50), default="pending")
  created_at = Column(String(100), nullable=False)


class TransactionModel(Base):
  __tablename__ = "transactions"
  id = Column(Integer, primary_key=True, index=True, autoincrement=True)
  user_id = Column(Integer, nullable=False)
  type = Column(String(50), nullable=False)
  amount = Column(Integer, nullable=False)
  booking_id = Column(Integer, nullable=False)
  timestamp = Column(String(100), nullable=False)


# Create tables in MySQL automatically
Base.metadata.create_all(bind=engine)


def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
  db.close()
