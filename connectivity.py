import os
from dotenv import load_dotenv
from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, Table, TypeDecorator, create_engine, inspect, join
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker, synonym

load_dotenv()

def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable '{name}'. Copy .env.example to .env.")
    return value

DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=_require_env("DB_USER"),
    password=_require_env("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=_require_env("DB_NAME"),
    query={"charset": "utf8mb4"},
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UpperInDB(TypeDecorator):
    """Handles uppercase storage in DB and lowercase in app."""
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return value.upper() if value is not None else None

    def process_result_value(self, value, dialect):
        return value.lower() if value is not None else None

def money():
    return Numeric(5, 2, asdecimal=False)

# ---------------- MODELS ----------------
class UserModel(Base):
    __tablename__ = "STUDENT"

    id = Column("STUDENT_ID", Integer, primary_key=True, autoincrement=True)
    name = Column("NAME", String(100), nullable=False)
    email = Column("EMAIL", String(100), unique=True, nullable=False)
    password = Column("PASSWORD", String(255), nullable=False, default="")
    department = Column("DEPARTMENT", String(150), nullable=False)
    availability = Column("AVAILABILITY", String(255), default="")
    credits = Column("CREDIT_BALANCE", money(), nullable=False, default=5)
    rating = Column("RATING", Numeric(3, 2, asdecimal=False), nullable=False, default=0.0)
    rating_count = Column("RATING_COUNT", Integer, nullable=False, default=0)

_skill_t = Table(
    "SKILL", Base.metadata,
    Column("SKILL_ID", Integer, primary_key=True, autoincrement=True),
    Column("SKILL_NAME", String(100), nullable=False),
    Column("CATEGORY", String(100), nullable=False, default="General"),
)
_student_skill_t = Table(
    "STUDENT_SKILL", Base.metadata,
    Column("STUDENT_ID", Integer, ForeignKey("STUDENT.STUDENT_ID"), primary_key=True),
    Column("SKILL_ID", Integer, ForeignKey("SKILL.SKILL_ID"), primary_key=True),
    Column("SKILL_TYPE", UpperInDB(20), primary_key=True),
)

class SkillModel(Base):
    __table__ = join(_skill_t, _student_skill_t, _skill_t.c.SKILL_ID == _student_skill_t.c.SKILL_ID)
    __mapper_args__ = {
        "properties": {
            "id": [_skill_t.c.SKILL_ID, _student_skill_t.c.SKILL_ID],
            "user_id": _student_skill_t.c.STUDENT_ID,
            "skill_name": _skill_t.c.SKILL_NAME,
            "skill_type": _student_skill_t.c.SKILL_TYPE,
        }
    }

class BookingModel(Base):
    __tablename__ = "BOOKING"

    id = Column("BOOKING_ID", Integer, primary_key=True, autoincrement=True)
    student_id = Column("LEARNER_ID", Integer, ForeignKey("STUDENT.STUDENT_ID"), nullable=False)
    tutor_id = Column("TUTOR_ID", Integer, ForeignKey("STUDENT.STUDENT_ID"), nullable=False)
    skill_id = Column("SKILL_ID", Integer, ForeignKey("SKILL.SKILL_ID"), nullable=False)
    date = Column("SESSION_DATE", String(20), nullable=False)
    start_time = Column("START_TIME", String(20), nullable=False)
    duration = Column("DURATION", Numeric(4, 2, asdecimal=False), nullable=False)
    status = Column("STATUS", UpperInDB(20), default="pending")
    credits = synonym("duration")

class TransactionModel(Base):
    __tablename__ = "CREDIT_TRANSACTION"

    id = Column("TRANSACTION_ID", Integer, primary_key=True, autoincrement=True)
    booking_id = Column("BOOKING_ID", Integer, ForeignKey("BOOKING.BOOKING_ID"), nullable=False)
    user_id = Column("STUDENT_ID", Integer, ForeignKey("STUDENT.STUDENT_ID"), nullable=False)
    type = Column("TRANSACTION_TYPE", UpperInDB(30), nullable=False)
    amount = Column("AMOUNT", money(), nullable=False)

# ---------------- SCHEMA VERIFICATION ----------------
_REQUIRED = {
    "STUDENT": {"STUDENT_ID", "NAME", "EMAIL", "PASSWORD", "DEPARTMENT", "AVAILABILITY", "CREDIT_BALANCE", "RATING", "RATING_COUNT"},
    "SKILL": {"SKILL_ID", "SKILL_NAME", "CATEGORY"},
    "STUDENT_SKILL": {"STUDENT_ID", "SKILL_ID", "SKILL_TYPE"},
    "BOOKING": {"BOOKING_ID", "LEARNER_ID", "TUTOR_ID", "SKILL_ID", "SESSION_DATE", "START_TIME", "DURATION", "STATUS"},
    "CREDIT_TRANSACTION": {"TRANSACTION_ID", "BOOKING_ID", "STUDENT_ID", "TRANSACTION_TYPE", "AMOUNT"},
}

def verify_schema():
    insp = inspect(engine)
    problems = []
    for table, cols in _REQUIRED.items():
        if not insp.has_table(table):
            problems.append(f"Table '{table}' is missing.")
            continue
        have = {c["name"].upper() for c in insp.get_columns(table)}
        for missing in sorted(cols - have):
            problems.append(f"Column '{table}.{missing}' is missing.")
    if problems:
        raise RuntimeError("Database schema mismatch:\n  - " + "\n  - ".join(problems) + "\nRun skillswap.sql first.")

verify_schema()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
