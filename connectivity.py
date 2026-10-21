import os

from dotenv import load_dotenv
from sqlalchemy import (
    Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Table, Time, TypeDecorator,
    create_engine, inspect, join,
)
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker, synonym

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


# Build the URL safely: URL.create escapes special characters in the password
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
    """The database stores 'OFFERED' / 'PENDING' (as in skillswap.sql);
    main.py works with lowercase 'offered' / 'pending'."""
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return value.upper() if value is not None else None

    def process_result_value(self, value, dialect):
        return value.lower() if value is not None else None


def money():
    # asdecimal=False -> plain numbers, so main.py's math and JSON work unchanged
    return Numeric(5, 2, asdecimal=False)


# ---------------- STUDENT -> UserModel ----------------
class UserModel(Base):
    __tablename__ = "STUDENT"

    id = Column("STUDENT_ID", Integer, primary_key=True, autoincrement=True)
    name = Column("NAME", String(100), nullable=False)
    email = Column("EMAIL", String(100), unique=True, nullable=False)
    # The API stores a password hash here, never the plain-text password.
    password = Column("PASSWORD", String(255), nullable=False, default="")
    department = Column("DEPARTMENT", String(150), nullable=False)
    availability = Column("AVAILABILITY", String(255), default="")
    credits = Column("CREDIT_BALANCE", money(), nullable=False, default=5)
    rating = Column("RATING", Numeric(3, 2, asdecimal=False), nullable=False, default=0.0)
    rating_count = Column("RATING_COUNT", Integer, nullable=False, default=0)


# ------- SKILL + STUDENT_SKILL -> SkillModel (one object, two tables) -------
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
    Column("LEVEL", String(20), nullable=True),
)


class SkillModel(Base):
    __table__ = join(_skill_t, _student_skill_t,
                     _skill_t.c.SKILL_ID == _student_skill_t.c.SKILL_ID)
    __mapper_args__ = {
        "properties": {
            "id": [_skill_t.c.SKILL_ID, _student_skill_t.c.SKILL_ID],
            "user_id": _student_skill_t.c.STUDENT_ID,
            "skill_name": _skill_t.c.SKILL_NAME,
            "skill_type": _student_skill_t.c.SKILL_TYPE,
        }
    }


# ---------------- BOOKING -> BookingModel ----------------
class BookingModel(Base):
    __tablename__ = "BOOKING"

    id = Column("BOOKING_ID", Integer, primary_key=True, autoincrement=True)
    student_id = Column("LEARNER_ID", Integer, ForeignKey("STUDENT.STUDENT_ID"), nullable=False)
    tutor_id = Column("TUTOR_ID", Integer, ForeignKey("STUDENT.STUDENT_ID"), nullable=False)
    skill_id = Column("SKILL_ID", Integer, ForeignKey("SKILL.SKILL_ID"), nullable=False)
    # Use actual SQL DATE/TIME types so Python receives date/time objects.
    date = Column("SESSION_DATE", Date, nullable=False)
    start_time = Column("START_TIME", Time, nullable=False)
    duration = Column("DURATION", Numeric(4, 2, asdecimal=False), nullable=False)
    status = Column("STATUS", UpperInDB(20), default="pending")
    # BOOKING has no CREDITS column: credits locked == duration, so alias it.
    credits = synonym("duration")


# ------------- CREDIT_TRANSACTION -> TransactionModel -------------
class TransactionModel(Base):
    __tablename__ = "CREDIT_TRANSACTION"

    id = Column("TRANSACTION_ID", Integer, primary_key=True, autoincrement=True)
    booking_id = Column("BOOKING_ID", Integer, ForeignKey("BOOKING.BOOKING_ID"), nullable=False)
    user_id = Column("STUDENT_ID", Integer, ForeignKey("STUDENT.STUDENT_ID"), nullable=False)
    type = Column("TRANSACTION_TYPE", UpperInDB(30), nullable=False)
    amount = Column("AMOUNT", money(), nullable=False)
    created = Column("TRANSACTION_DATE", DateTime)


# Names expected by main.py for the two skill tables.
SKILL_T = _skill_t
STUDENT_SKILL_T = _student_skill_t


# ---------------- REVIEW -> ReviewModel ----------------
class ReviewModel(Base):
    __tablename__ = "REVIEW"

    id = Column("REVIEW_ID", Integer, primary_key=True, autoincrement=True)
    booking_id = Column("BOOKING_ID", Integer, ForeignKey("BOOKING.BOOKING_ID"), nullable=False, unique=True)
    reviewer_id = Column("REVIEWER_ID", Integer, ForeignKey("STUDENT.STUDENT_ID"), nullable=False)
    tutor_id = Column("TUTOR_ID", Integer, ForeignKey("STUDENT.STUDENT_ID"), nullable=False)
    rating = Column("RATING", Numeric(2, 1, asdecimal=False), nullable=False)
    comment = Column("COMMENT", String(500), default="")


# ---------------- DISPUTE -> DisputeModel ----------------
class DisputeModel(Base):
    __tablename__ = "DISPUTE"

    id = Column("DISPUTE_ID", Integer, primary_key=True, autoincrement=True)
    booking_id = Column("BOOKING_ID", Integer, ForeignKey("BOOKING.BOOKING_ID"), nullable=False)
    user_id = Column("STUDENT_ID", Integer, ForeignKey("STUDENT.STUDENT_ID"), nullable=False)
    reason = Column("REASON", String(500), nullable=False)
    status = Column("STATUS", String(20), nullable=False, default="OPEN")


# ------------- Startup check: clear error instead of a 500 later -------------
_REQUIRED = {
    "STUDENT": {"STUDENT_ID", "NAME", "EMAIL", "PASSWORD", "DEPARTMENT",
                "AVAILABILITY", "CREDIT_BALANCE", "RATING", "RATING_COUNT"},
    "SKILL": {"SKILL_ID", "SKILL_NAME", "CATEGORY"},
    "STUDENT_SKILL": {"STUDENT_ID", "SKILL_ID", "SKILL_TYPE", "LEVEL"},
    "BOOKING": {"BOOKING_ID", "LEARNER_ID", "TUTOR_ID", "SKILL_ID",
                "SESSION_DATE", "START_TIME", "DURATION", "STATUS"},
    "CREDIT_TRANSACTION": {"TRANSACTION_ID", "BOOKING_ID", "STUDENT_ID",
                           "TRANSACTION_TYPE", "AMOUNT"},
    "REVIEW": {"REVIEW_ID", "BOOKING_ID", "REVIEWER_ID", "TUTOR_ID", "RATING", "COMMENT"},
    "DISPUTE": {"DISPUTE_ID", "BOOKING_ID", "STUDENT_ID", "REASON", "STATUS"},
}


def verify_schema():
    insp = inspect(engine)
    problems = []
    for table, cols in _REQUIRED.items():
        if not insp.has_table(table):
            problems.append(f"table {table} is missing")
            continue
        have = {c["name"].upper() for c in insp.get_columns(table)}
        for missing in sorted(cols - have):
            problems.append(f"{table}.{missing} is missing")
    if problems:
        raise RuntimeError("Database does not match connectivity.py:\n  - "
                           + "\n  - ".join(problems)
                           + "\nRun skillswap.sql first.")
verify_schema()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

