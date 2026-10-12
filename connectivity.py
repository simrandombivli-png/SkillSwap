import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import Column, Float, Integer, String, Text, create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

# Load variables from a local .env file (never committed to git)
load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing environment variable '{name}'. "
            "Copy .env.example to .env and fill in your values."
        )
    return value


def _now() -> str:
    """UTC timestamp as an ISO string (columns below are String-based)."""
    return datetime.now(timezone.utc).isoformat()


# Build the URL safely: URL.create escapes special characters in the password
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=_require_env("DB_USER"),
    password=_require_env("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=_require_env("DB_NAME"),
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
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
    # Default added: main.py never sets this, so inserts used to fail
    created_at = Column(String(100), nullable=False, default=_now)


class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    type = Column(String(50), nullable=False)
    amount = Column(Integer, nullable=False)
    booking_id = Column(Integer, nullable=False)
    # Default added: main.py never sets this, so inserts used to fail
    timestamp = Column(String(100), nullable=False, default=_now)


# Create tables in MySQL automatically
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
