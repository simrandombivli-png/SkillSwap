from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from connectivity import SessionLocal, get_db, UserModel, SkillModel, BookingModel, TransactionModel

app = FastAPI(
    title="SkillSwap API",
    description="Peer-to-Peer Student Time Bank",
    version="1.0"
)


# ============================================================
# REQUEST MODELS
# ============================================================

class UserCreate(BaseModel):
    name: str
    email: str
    department: str
    availability: List[str] = []


class SkillCreate(BaseModel):
    skill_name: str
    skill_type: str


class BookingCreate(BaseModel):
    student_id: int
    tutor_id: int
    skill_id: int
    date: str
    start_time: str
    duration: int


class RatingCreate(BaseModel):
    rating: float
    review: Optional[str] = None


class DisputeCreate(BaseModel):
    reason: str


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "message": "SkillSwap API is running",
        "status": "success"
    }


# ============================================================
# USER APIs
# ============================================================

@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check duplicate email in MySQL database
    existing_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Convert availability list to comma-separated string for DB storage
    avail_str = ",".join(user.availability) if isinstance(user.availability, list) else user.availability

    new_user = UserModel(
        name=user.name,
        email=user.email,
        department=user.department,
        availability=avail_str,
        credits=5,
        rating=0.0
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "department": new_user.department,
            "availability": new_user.availability.split(",") if new_user.availability else [],
            "credits": new_user.credits,
            "rating": new_user.rating
        }
    }


@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "department": user.department,
        "availability": user.availability.split(",") if user.availability else [],
        "credits": user.credits,
        "rating": user.rating
    }


# ============================================================
# SKILL APIs
# ============================================================

@app.post("/users/{user_id}/skills")
def add_skill(user_id: int, skill: SkillCreate, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if skill.skill_type not in ["offered", "requested"]:
        raise HTTPException(
            status_code=400,
            detail="skill_type must be 'offered' or 'requested'"
        )

    new_skill = SkillModel(
        user_id=user_id,
        skill_name=skill.skill_name,
        skill_type=skill.skill_type
    )

    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)

    return {
        "message": "Skill added successfully",
        "skill": {
            "id": new_skill.id,
            "user_id": new_skill.user_id,
            "skill_name": new_skill.skill_name,
            "skill_type": new_skill.skill_type
        }
    }


@app.get("/users/{user_id}/skills")
def get_user_skills(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    skills = db.query(SkillModel).filter(SkillModel.user_id == user_id).all()
    return skills


@app.get("/skills")
def get_all_skills(db: Session = Depends(get_db)):
    return db.query(SkillModel).all()


# ============================================================
# PEER MATCHING
# ============================================================

@app.get("/matches")
def find_matches(
    skill_name: str,
    availability: Optional[str] = None,
    min_rating: float = 0,
    db: Session = Depends(get_db)
):
    offered_skills = db.query(SkillModel).filter(
        SkillModel.skill_type == "offered",
        SkillModel.skill_name.ilike(skill_name)
    ).all()

    matches = []
    for skill in offered_skills:
        tutor = db.query(UserModel).filter(UserModel.id == skill.user_id).first()
        if not tutor:
            continue

        if tutor.rating < min_rating:
            continue

        tutor_avail = tutor.availability.split(",") if tutor.availability else []
        if availability and availability not in tutor_avail:
            continue

        matches.append({
            "user_id": tutor.id,
            "name": tutor.name,
            "department": tutor.department,
            "skill": skill.skill_name,
            "rating": tutor.rating,
            "availability": tutor_avail
        })

    matches.sort(key=lambda x: x["rating"], reverse=True)

    return {
        "count": len(matches),
        "matches": matches
    }


# ============================================================
# CREDIT APIs
# ============================================================

@app.get("/users/{user_id}/credits")
def get_credits(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "user_id": user_id,
        "credits": user.credits
    }


@app.get("/users/{user_id}/transactions")
def get_transactions(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return db.query(TransactionModel).filter(TransactionModel.user_id == user_id).all()


# ============================================================
# BOOKING API
# ============================================================

@app.post("/bookings")
def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    student = db.query(UserModel).filter(UserModel.id == booking.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    tutor = db.query(UserModel).filter(UserModel.id == booking.tutor_id).first()
    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor not found")

    if booking.student_id == booking.tutor_id:
        raise HTTPException(status_code=400, detail="Student and tutor cannot be the same")

    if booking.duration not in [1, 2]:
        raise HTTPException(status_code=400, detail="Duration must be 1 or 2 hours")

    if student.credits < booking.duration:
        raise HTTPException(status_code=400, detail="Insufficient Time Credits")

    # Check tutor's skill
    skill = db.query(SkillModel).filter(
        SkillModel.id == booking.skill_id,
        SkillModel.user_id == booking.tutor_id,
        SkillModel.skill_type == "offered"
    ).first()

    if not skill:
        raise HTTPException(status_code=400, detail="Tutor does not offer this skill")

    # Lock escrow credits
    student.credits -= booking.duration

    # Create Booking
    new_booking = BookingModel(
        student_id=booking.student_id,
        tutor_id=booking.tutor_id,
        skill_id=booking.skill_id,
        date=booking.date,
        start_time=booking.start_time,
        duration=booking.duration,
        credits=booking.duration,
        status="pending"
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    # Log Transaction
    transaction = TransactionModel(
        user_id=booking.student_id,
        type="escrow_lock",
        amount=booking.duration,
        booking_id=new_booking.id
    )
    db.add(transaction)
    db.commit()

    return {
        "message": "Booking created successfully",
        "escrow": f"{booking.duration} credit(s) locked",
        "booking": new_booking
    }


# ============================================================
# GET BOOKING
# ============================================================

@app.get("/bookings/{booking_id}")
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(BookingModel).filter(BookingModel.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@app.get("/users/{user_id}/bookings")
def get_user_bookings(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return db.query(BookingModel).filter(
        (BookingModel.student_id == user_id) | (BookingModel.tutor_id == user_id)
    ).all()


# ============================================================
# CONFIRM BOOKING
# ============================================================

@app.post("/bookings/{booking_id}/confirm")
def confirm_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(BookingModel).filter(BookingModel.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status != "pending":
        raise HTTPException(status_code=400, detail="Booking cannot be confirmed")

    booking.status = "confirmed"
    db.commit()
    db.refresh(booking)

    return {
        "message": "Booking confirmed",
        "booking": booking
    }


# ============================================================
# COMPLETE SESSION
# ============================================================

@app.post("/bookings/{booking_id}/complete")
def complete_session(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(BookingModel).filter(BookingModel.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status != "confirmed":
        raise HTTPException(status_code=400, detail="Booking must be confirmed first")

    tutor = db.query(UserModel).filter(UserModel.id == booking.tutor_id).first()
    tutor.credits += booking.credits
    booking.status = "completed"

    transaction = TransactionModel(
        user_id=tutor.id,
        type="escrow_release",
        amount=booking.credits,
        booking_id=booking_id
    )

    db.add(transaction)
    db.commit()

    return {
        "message": "Session completed successfully",
        "credits_transferred": booking.credits,
        "booking": booking
    }


# ============================================================
# RATING API
# ============================================================

@app.post("/bookings/{booking_id}/rating")
def rate_tutor(booking_id: int, rating: RatingCreate, db: Session = Depends(get_db)):
    if rating.rating < 1 or rating.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    booking = db.query(BookingModel).filter(BookingModel.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status != "completed":
        raise HTTPException(status_code=400, detail="Session must be completed first")

    tutor = db.query(UserModel).filter(UserModel.id == booking.tutor_id).first()
    tutor.rating = round(float(rating.rating), 2)

    db.commit()

    return {
        "message": "Rating submitted successfully",
        "new_tutor_rating": tutor.rating
    }


# ============================================================
# ANALYTICS API
# ============================================================

@app.get("/users/{user_id}/analytics")
def get_analytics(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    completed_bookings = db.query(BookingModel).filter(
        BookingModel.status == "completed"
    ).all()

    hours_taught = sum(b.duration for b in completed_bookings if b.tutor_id == user_id)
    hours_received = sum(b.duration for b in completed_bookings if b.student_id == user_id)

    return {
        "user_id": user_id,
        "hours_taught": hours_taught,
        "hours_received": hours_received,
        "net_learning_balance": hours_received - hours_taught
    }
