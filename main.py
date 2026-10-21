from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from pwdlib import PasswordHash
from pydantic import BaseModel
from sqlalchemy import and_, delete, func, insert, or_, select
from sqlalchemy.orm import Session

from connectivity import (
    get_db, UserModel, BookingModel, TransactionModel, ReviewModel,
    DisputeModel, SKILL_T, STUDENT_SKILL_T,
)

password_hash = PasswordHash.recommended()

app = FastAPI(title="SkillSwap API", description="Peer-to-Peer Student Time Bank", version="1.0")

ACTIVE = ("pending", "confirmed")
ESCROWED = ("pending", "confirmed", "disputed")


# ============================================================
# REQUEST MODELS
# ============================================================
class UserCreate(BaseModel):
    name: str
    email: str
    department: str
    password: str
    availability: List[str] = []


class LoginRequest(BaseModel):
    email: str
    password: str


class SkillCreate(BaseModel):
    skill_name: str
    skill_type: str
    category: str = "General"
    level: Optional[str] = None


class BookingCreate(BaseModel):
    student_id: int
    tutor_id: int
    skill_id: int
    date: str
    start_time: str
    duration: int


class ActorBody(BaseModel):
    user_id: int


class ReviewBody(BaseModel):
    user_id: int
    rating: float
    comment: Optional[str] = None


class DisputeBody(BaseModel):
    user_id: int
    reason: str


# ============================================================
# HELPERS
# ============================================================
def user_out(u: UserModel):
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "department": u.department,
        "availability": [a for a in (u.availability or "").split(",") if a],
        "credits": float(u.credits),
        "rating": float(u.rating),
        "rating_count": u.rating_count,
    }


def get_user_or_404(db: Session, uid: int, label: str = "User") -> UserModel:
    u = db.query(UserModel).filter(UserModel.id == uid).first()
    if not u:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return u


def get_booking_or_404(db: Session, bid: int) -> BookingModel:
    b = db.query(BookingModel).filter(BookingModel.id == bid).first()
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")
    return b


def bookings_out(db: Session, rows):
    if not rows:
        return []
    uids = {b.student_id for b in rows} | {b.tutor_id for b in rows}
    names = {u.id: u.name for u in db.query(UserModel).filter(UserModel.id.in_(uids)).all()}
    sids = {b.skill_id for b in rows}
    skills = {sid: nm for sid, nm in db.execute(
        select(SKILL_T.c.SKILL_ID, SKILL_T.c.SKILL_NAME).where(SKILL_T.c.SKILL_ID.in_(sids)))}
    reviewed = {r[0] for r in db.query(ReviewModel.booking_id)
                .filter(ReviewModel.booking_id.in_([b.id for b in rows])).all()}
    out = []
    for b in rows:
        out.append({
            "id": b.id,
            "learner_id": b.student_id,
            "tutor_id": b.tutor_id,
            "learner": names.get(b.student_id, "?"),
            "tutor": names.get(b.tutor_id, "?"),
            "skill": skills.get(b.skill_id, "?"),
            "date": b.date.strftime("%Y-%m-%d"),
            "time": b.start_time.strftime("%H:%M"),
            "hours": float(b.duration),
            "status": b.status,
            "reviewed": b.id in reviewed,
        })
    return out


# ============================================================
# HOME
# ============================================================
@app.get("/")
def home():
    return {"message": "SkillSwap API is running", "status": "success"}


# ============================================================
# AUTH / USERS
# ============================================================
@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    email = user.email.strip().lower()
    if not user.name.strip() or not email or not user.department.strip() or not user.password.strip():
        raise HTTPException(status_code=400, detail="Fill all fields")
    if db.query(UserModel).filter(func.lower(UserModel.email) == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = UserModel(
        name=user.name.strip(),
        email=email,
        password=password_hash.hash(user.password),
        department=user.department.strip(),
        availability=",".join(user.availability),
        credits=5,
        rating=0.0,
        rating_count=0,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "user": user_out(new_user)}


@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    u = db.query(UserModel).filter(func.lower(UserModel.email) == email).first()
    ok = False
    if u:
        try:
            ok = bool(u.password) and password_hash.verify(req.password, u.password)
        except Exception:
            ok = False
    if not ok:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"message": "Login successful", "user": user_out(u)}


@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    return user_out(get_user_or_404(db, user_id))


# ============================================================
# SKILLS
# ============================================================
@app.get("/skills")
def get_all_skills(db: Session = Depends(get_db)):
    rows = db.execute(select(SKILL_T.c.SKILL_ID, SKILL_T.c.SKILL_NAME, SKILL_T.c.CATEGORY)
                      .order_by(SKILL_T.c.SKILL_NAME)).all()
    return [{"skill_id": r[0], "skill_name": r[1], "category": r[2]} for r in rows]


@app.post("/users/{user_id}/skills")
def add_skill(user_id: int, skill: SkillCreate, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    stype = skill.skill_type.lower()
    if stype not in ("offered", "requested"):
        raise HTTPException(status_code=400, detail="skill_type must be 'offered' or 'requested'")
    name = skill.skill_name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Skill name is required")

    row = db.execute(select(SKILL_T.c.SKILL_ID).where(
        func.lower(SKILL_T.c.SKILL_NAME) == name.lower())).first()
    if row:
        sid = row[0]
    else:
        res = db.execute(insert(SKILL_T).values(SKILL_NAME=name, CATEGORY=skill.category or "General"))
        sid = res.inserted_primary_key[0]

    dup = db.execute(select(STUDENT_SKILL_T.c.SKILL_ID).where(and_(
        STUDENT_SKILL_T.c.STUDENT_ID == user_id,
        STUDENT_SKILL_T.c.SKILL_ID == sid,
        STUDENT_SKILL_T.c.SKILL_TYPE == stype))).first()
    if dup:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"You already have this skill as {stype}")

    level = skill.level if stype == "offered" else None
    if stype == "offered" and level not in ("Beginner", "Intermediate", "Expert"):
        raise HTTPException(status_code=400, detail="Choose Beginner, Intermediate, or Expert for an offered skill")
    db.execute(insert(STUDENT_SKILL_T).values(STUDENT_ID=user_id, SKILL_ID=sid, SKILL_TYPE=stype, LEVEL=level))
    db.commit()
    return {"message": "Skill added successfully",
            "skill": {"skill_id": sid, "skill_name": name, "skill_type": stype, "level": level}}


@app.get("/users/{user_id}/skills")
def get_user_skills(user_id: int, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    rows = db.execute(
        select(SKILL_T.c.SKILL_ID, SKILL_T.c.SKILL_NAME, STUDENT_SKILL_T.c.SKILL_TYPE, STUDENT_SKILL_T.c.LEVEL)
        .join(STUDENT_SKILL_T, STUDENT_SKILL_T.c.SKILL_ID == SKILL_T.c.SKILL_ID)
        .where(STUDENT_SKILL_T.c.STUDENT_ID == user_id)
        .order_by(SKILL_T.c.SKILL_NAME)).all()
    return [{"skill_id": r[0], "skill_name": r[1], "skill_type": r[2], "level": r[3]} for r in rows]


@app.delete("/users/{user_id}/skills/{skill_id}/{skill_type}")
def remove_skill(user_id: int, skill_id: int, skill_type: str, db: Session = Depends(get_db)):
    db.execute(delete(STUDENT_SKILL_T).where(and_(
        STUDENT_SKILL_T.c.STUDENT_ID == user_id,
        STUDENT_SKILL_T.c.SKILL_ID == skill_id,
        STUDENT_SKILL_T.c.SKILL_TYPE == skill_type.lower())))
    db.commit()
    return {"message": "Skill removed"}


# ============================================================
# PEER MATCHING
# ============================================================
@app.get("/matches")
def find_matches(
    skill_name: str = "",
    availability: Optional[str] = None,
    min_rating: float = 0,
    exclude_user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = (select(STUDENT_SKILL_T.c.STUDENT_ID, SKILL_T.c.SKILL_ID,
                SKILL_T.c.SKILL_NAME, STUDENT_SKILL_T.c.LEVEL)
         .join(SKILL_T, SKILL_T.c.SKILL_ID == STUDENT_SKILL_T.c.SKILL_ID)
         .where(STUDENT_SKILL_T.c.SKILL_TYPE == "offered"))
    if skill_name.strip():
        q = q.where(func.lower(SKILL_T.c.SKILL_NAME).like(f"%{skill_name.strip().lower()}%"))

    matches = []
    for tutor_id, sid, sname, level in db.execute(q).all():
        if exclude_user_id is not None and tutor_id == exclude_user_id:
            continue
        tutor = db.query(UserModel).filter(UserModel.id == tutor_id).first()
        if not tutor or float(tutor.rating) < min_rating:
            continue
        avail = [a for a in (tutor.availability or "").split(",") if a]
        if availability and availability not in avail:
            continue
        matches.append({
            "user_id": tutor.id, "name": tutor.name, "department": tutor.department,
            "skill_id": sid, "skill": sname, "level": level, "rating": float(tutor.rating),
            "rating_count": tutor.rating_count, "availability": avail,
        })
    matches.sort(key=lambda m: m["rating"], reverse=True)
    return {"count": len(matches), "matches": matches}


# ============================================================
# WALLET
# ============================================================
@app.get("/users/{user_id}/credits")
def get_credits(user_id: int, db: Session = Depends(get_db)):
    return {"user_id": user_id, "credits": float(get_user_or_404(db, user_id).credits)}


@app.get("/users/{user_id}/wallet")
def get_wallet(user_id: int, db: Session = Depends(get_db)):
    user = get_user_or_404(db, user_id)
    escrow = db.query(func.coalesce(func.sum(BookingModel.duration), 0)).filter(
        BookingModel.student_id == user_id, BookingModel.status.in_(ESCROWED)).scalar()
    txs = db.query(TransactionModel).filter(TransactionModel.user_id == user_id) \
        .order_by(TransactionModel.id.desc()).all()
    return {
        "credits": float(user.credits),
        "escrow": float(escrow or 0),
        "transactions": [{
            "id": t.id, "booking_id": t.booking_id, "type": t.type, "amount": float(t.amount),
            "date": t.created.strftime("%d %b %Y %H:%M") if t.created else "",
        } for t in txs],
    }


@app.get("/users/{user_id}/transactions")
def get_transactions(user_id: int, db: Session = Depends(get_db)):
    return get_wallet(user_id, db)["transactions"]


# ============================================================
# BOOKINGS
# ============================================================
@app.post("/bookings")
def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    student = get_user_or_404(db, booking.student_id, "Student")
    get_user_or_404(db, booking.tutor_id, "Tutor")

    if booking.student_id == booking.tutor_id:
        raise HTTPException(status_code=400, detail="Student and tutor cannot be the same")
    if booking.duration not in (1, 2):
        raise HTTPException(status_code=400, detail="Duration must be 1 or 2 hours")
    try:
        when = datetime.strptime(f"{booking.date} {booking.start_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Use date YYYY-MM-DD and time HH:MM")
    if when < datetime.now():
        raise HTTPException(status_code=400, detail="Choose a future date and time")
    if float(student.credits) < booking.duration:
        raise HTTPException(status_code=400, detail="Insufficient Time Credits")

    offers = db.execute(select(STUDENT_SKILL_T.c.SKILL_ID).where(and_(
        STUDENT_SKILL_T.c.STUDENT_ID == booking.tutor_id,
        STUDENT_SKILL_T.c.SKILL_ID == booking.skill_id,
        STUDENT_SKILL_T.c.SKILL_TYPE == "offered"))).first()
    if not offers:
        raise HTTPException(status_code=400, detail="Tutor does not offer this skill")

    people = (booking.student_id, booking.tutor_id)
    others = db.query(BookingModel).filter(
        BookingModel.date == when.date(),
        BookingModel.status.in_(ACTIVE),
        or_(BookingModel.student_id.in_(people), BookingModel.tutor_id.in_(people)),
    ).all()
    for o in others:
        o_start = datetime.combine(o.date, o.start_time)
        if when < o_start + timedelta(hours=float(o.duration)) and o_start < when + timedelta(hours=booking.duration):
            raise HTTPException(status_code=400,
                                detail="You or the tutor already have a booking that overlaps this time")

    student.credits = float(student.credits) - booking.duration  # lock escrow
    new_booking = BookingModel(
        student_id=booking.student_id, tutor_id=booking.tutor_id, skill_id=booking.skill_id,
        date=when.date(), start_time=when.time(), duration=booking.duration, status="pending")
    db.add(new_booking)
    db.flush()
    db.add(TransactionModel(user_id=booking.student_id, type="escrow_lock",
                            amount=booking.duration, booking_id=new_booking.id))
    db.commit()
    db.refresh(new_booking)
    return {"message": "Booking created successfully",
            "escrow": f"{booking.duration} credit(s) locked",
            "booking": bookings_out(db, [new_booking])[0]}


@app.get("/bookings/{booking_id}")
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    return bookings_out(db, [get_booking_or_404(db, booking_id)])[0]


@app.get("/users/{user_id}/bookings")
def get_user_bookings(user_id: int, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    rows = db.query(BookingModel).filter(
        or_(BookingModel.student_id == user_id, BookingModel.tutor_id == user_id)
    ).order_by(BookingModel.id.desc()).all()
    return bookings_out(db, rows)


@app.post("/bookings/{booking_id}/confirm")
def confirm_booking(booking_id: int, body: ActorBody, db: Session = Depends(get_db)):
    b = get_booking_or_404(db, booking_id)
    if b.tutor_id != body.user_id:
        raise HTTPException(status_code=403, detail="Only the teacher can confirm a session")
    if b.status != "pending":
        raise HTTPException(status_code=400, detail="Only pending sessions can be confirmed")
    b.status = "confirmed"
    db.commit()
    return {"message": "Booking confirmed"}


@app.post("/bookings/{booking_id}/complete")
def complete_session(booking_id: int, body: ActorBody, db: Session = Depends(get_db)):
    b = get_booking_or_404(db, booking_id)
    if b.student_id != body.user_id:
        raise HTTPException(status_code=403, detail="Only the learner can complete a session")
    if b.status != "confirmed":
        raise HTTPException(status_code=400, detail="Session must be confirmed first")
    tutor = get_user_or_404(db, b.tutor_id, "Tutor")
    tutor.credits = float(tutor.credits) + float(b.duration)
    b.status = "completed"
    db.add(TransactionModel(user_id=tutor.id, type="escrow_release",
                            amount=b.duration, booking_id=b.id))
    db.commit()
    return {"message": "Session completed", "credits_transferred": float(b.duration)}


@app.post("/bookings/{booking_id}/cancel")
def cancel_booking(booking_id: int, body: ActorBody, db: Session = Depends(get_db)):
    b = get_booking_or_404(db, booking_id)
    if body.user_id not in (b.student_id, b.tutor_id):
        raise HTTPException(status_code=403, detail="Not your session")
    if b.status not in ACTIVE:
        raise HTTPException(status_code=400, detail="Only pending or confirmed sessions can be cancelled")
    learner = get_user_or_404(db, b.student_id, "Learner")
    learner.credits = float(learner.credits) + float(b.duration)
    b.status = "cancelled"
    db.add(TransactionModel(user_id=learner.id, type="refund", amount=b.duration, booking_id=b.id))
    db.commit()
    return {"message": "Session cancelled", "refunded": float(b.duration)}


@app.post("/bookings/{booking_id}/dispute")
def dispute_booking(booking_id: int, body: DisputeBody, db: Session = Depends(get_db)):
    b = get_booking_or_404(db, booking_id)
    if body.user_id not in (b.student_id, b.tutor_id):
        raise HTTPException(status_code=403, detail="Not your session")
    if b.status not in ACTIVE:
        raise HTTPException(status_code=400, detail="Only pending or confirmed sessions can be disputed")
    if not body.reason.strip():
        raise HTTPException(status_code=400, detail="Describe the issue first")
    db.add(DisputeModel(booking_id=b.id, user_id=body.user_id, reason=body.reason.strip()[:500], status="OPEN"))
    b.status = "disputed"
    db.commit()
    return {"message": "Dispute submitted. Credits stay in escrow until resolved."}


@app.post("/bookings/{booking_id}/rating")
def rate_tutor(booking_id: int, body: ReviewBody, db: Session = Depends(get_db)):
    if body.rating < 1 or body.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    b = get_booking_or_404(db, booking_id)
    if b.student_id != body.user_id:
        raise HTTPException(status_code=403, detail="Only the learner can review this session")
    if b.status != "completed":
        raise HTTPException(status_code=400, detail="Session must be completed first")
    if db.query(ReviewModel).filter(ReviewModel.booking_id == booking_id).first():
        raise HTTPException(status_code=400, detail="You already reviewed this session")

    tutor = get_user_or_404(db, b.tutor_id, "Tutor")
    db.add(ReviewModel(booking_id=b.id, reviewer_id=b.student_id, tutor_id=b.tutor_id,
                       rating=round(body.rating, 1), comment=(body.comment or "")[:500]))
    n = tutor.rating_count
    tutor.rating = round((float(tutor.rating) * n + body.rating) / (n + 1), 2)
    tutor.rating_count = n + 1
    db.commit()
    return {"message": "Rating submitted successfully", "new_tutor_rating": float(tutor.rating)}


# ============================================================
# ANALYTICS
# ============================================================
@app.get("/users/{user_id}/analytics")
def get_analytics(user_id: int, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)

    def total(col):
        return float(db.query(func.coalesce(func.sum(BookingModel.duration), 0)).filter(
            col == user_id, BookingModel.status == "completed").scalar() or 0)

    taught, received = total(BookingModel.tutor_id), total(BookingModel.student_id)
    return {"user_id": user_id, "hours_taught": taught, "hours_received": received,
            "net_learning_balance": received - taught}


@app.get("/top-teachers")
def top_teachers(db: Session = Depends(get_db)):
    rows = db.query(BookingModel.tutor_id, func.count(BookingModel.id), func.sum(BookingModel.duration)) \
        .filter(BookingModel.status == "completed") \
        .group_by(BookingModel.tutor_id) \
        .order_by(func.sum(BookingModel.duration).desc()).limit(5).all()
    out = []
    for tid, n, hrs in rows:
        u = db.query(UserModel).filter(UserModel.id == tid).first()
        if u:
            out.append({"name": u.name, "sessions": n, "hours": float(hrs), "rating": float(u.rating)})
    return out
