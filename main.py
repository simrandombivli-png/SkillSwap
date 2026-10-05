from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from connectivity import SessionLocal, get_db, UserModel, SkillModel, BookingModel, TransactionModel
app = FastAPI(
    title="SkillSwap API",
    description="Peer-to-Peer Student Time Bank",
    version="1.0"
)


# ============================================================
# TEMPORARY DATABASE
# ============================================================

users = {}
skills = []
bookings = []
transactions = []
ratings = []
disputes = []

next_user_id = 1
next_skill_id = 1
next_booking_id = 1


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
def create_user(user: UserCreate):

    global next_user_id

    # Check duplicate email
    for existing_user in users.values():

        if existing_user["email"] == user.email:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

    new_user = {
        "id": next_user_id,
        "name": user.name,
        "email": user.email,
        "department": user.department,
        "availability": user.availability,

        # Starting credits for demonstration
        "credits": 5,

        "rating": 0,
        "rating_count": 0
    }

    users[next_user_id] = new_user

    next_user_id += 1

    return {
        "message": "User registered successfully",
        "user": new_user
    }


@app.get("/users/{user_id}")
def get_user(user_id: int):

    if user_id not in users:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return users[user_id]


# ============================================================
# SKILL APIs
# ============================================================

@app.post("/users/{user_id}/skills")
def add_skill(
    user_id: int,
    skill: SkillCreate
):

    global next_skill_id

    if user_id not in users:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if skill.skill_type not in ["offered", "requested"]:
        raise HTTPException(
            status_code=400,
            detail="skill_type must be 'offered' or 'requested'"
        )

    new_skill = {
        "id": next_skill_id,
        "user_id": user_id,
        "skill_name": skill.skill_name,
        "skill_type": skill.skill_type
    }

    skills.append(new_skill)

    next_skill_id += 1

    return {
        "message": "Skill added successfully",
        "skill": new_skill
    }


@app.get("/users/{user_id}/skills")
def get_user_skills(user_id: int):

    if user_id not in users:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return [
        skill
        for skill in skills
        if skill["user_id"] == user_id
    ]


@app.get("/skills")
def get_all_skills():
    return skills


# ============================================================
# PEER MATCHING
# ============================================================

@app.get("/matches")
def find_matches(
    skill_name: str,
    availability: Optional[str] = None,
    min_rating: float = 0
):

    matches = []

    for skill in skills:

        # Only look at skills people offer
        if skill["skill_type"] != "offered":
            continue

        # Check skill name
        if skill["skill_name"].lower() != skill_name.lower():
            continue

        tutor = users[skill["user_id"]]

        # Check rating
        if tutor["rating"] < min_rating:
            continue

        # Check availability
        if availability:

            if availability not in tutor["availability"]:
                continue

        matches.append({
            "user_id": tutor["id"],
            "name": tutor["name"],
            "department": tutor["department"],
            "skill": skill["skill_name"],
            "rating": tutor["rating"],
            "availability": tutor["availability"]
        })

    # Highest-rated tutors first
    matches.sort(
        key=lambda x: x["rating"],
        reverse=True
    )

    return {
        "count": len(matches),
        "matches": matches
    }


# ============================================================
# CREDIT APIs
# ============================================================

@app.get("/users/{user_id}/credits")
def get_credits(user_id: int):

    if user_id not in users:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "user_id": user_id,
        "credits": users[user_id]["credits"]
    }


@app.get("/users/{user_id}/transactions")
def get_transactions(user_id: int):

    if user_id not in users:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return [
        transaction
        for transaction in transactions
        if transaction["user_id"] == user_id
    ]


# ============================================================
# BOOKING API
# ============================================================

@app.post("/bookings")
def create_booking(booking: BookingCreate):

    global next_booking_id

    # Check student
    if booking.student_id not in users:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    # Check tutor
    if booking.tutor_id not in users:
        raise HTTPException(
            status_code=404,
            detail="Tutor not found"
        )

    # Student and tutor cannot be same
    if booking.student_id == booking.tutor_id:
        raise HTTPException(
            status_code=400,
            detail="Student and tutor cannot be the same"
        )

    # Only 1 or 2 hour sessions
    if booking.duration not in [1, 2]:
        raise HTTPException(
            status_code=400,
            detail="Duration must be 1 or 2 hours"
        )

    student = users[booking.student_id]

    # ========================================================
    # CREDIT CHECK
    # ========================================================

    if student["credits"] < booking.duration:
        raise HTTPException(
            status_code=400,
            detail="Insufficient Time Credits"
        )

    # ========================================================
    # CHECK TUTOR'S SKILL
    # ========================================================

    valid_skill = any(
        skill["id"] == booking.skill_id
        and skill["user_id"] == booking.tutor_id
        and skill["skill_type"] == "offered"
        for skill in skills
    )

    if not valid_skill:
        raise HTTPException(
            status_code=400,
            detail="Tutor does not offer this skill"
        )

    # ========================================================
    # SCHEDULE CONFLICT CHECK
    # ========================================================

    for existing_booking in bookings:

        if existing_booking["status"] not in [
            "pending",
            "confirmed"
        ]:
            continue

        if existing_booking["date"] != booking.date:
            continue

        if existing_booking["start_time"] != booking.start_time:
            continue

        # Check student conflict
        if existing_booking["student_id"] == booking.student_id:

            raise HTTPException(
                status_code=400,
                detail="Student already has a booking at this time"
            )

        # Check tutor conflict
        if existing_booking["tutor_id"] == booking.tutor_id:

            raise HTTPException(
                status_code=400,
                detail="Tutor already has a booking at this time"
            )

    # ========================================================
    # ESCROW
    # ========================================================

    # Remove credits from student's available balance
    student["credits"] -= booking.duration

    # Record escrow transaction
    transactions.append({
        "user_id": booking.student_id,
        "type": "escrow_lock",
        "amount": booking.duration,
        "booking_id": next_booking_id,
        "timestamp": datetime.now().isoformat()
    })

    # ========================================================
    # CREATE BOOKING
    # ========================================================

    new_booking = {
        "id": next_booking_id,
        "student_id": booking.student_id,
        "tutor_id": booking.tutor_id,
        "skill_id": booking.skill_id,
        "date": booking.date,
        "start_time": booking.start_time,
        "duration": booking.duration,
        "credits": booking.duration,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }

    bookings.append(new_booking)

    next_booking_id += 1

    return {
        "message": "Booking created successfully",
        "escrow": f"{booking.duration} credit(s) locked",
        "booking": new_booking
    }


# ============================================================
# GET BOOKING
# ============================================================

@app.get("/bookings/{booking_id}")
def get_booking(booking_id: int):

    for booking in bookings:

        if booking["id"] == booking_id:
            return booking

    raise HTTPException(
        status_code=404,
        detail="Booking not found"
    )


@app.get("/users/{user_id}/bookings")
def get_user_bookings(user_id: int):

    if user_id not in users:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return [
        booking
        for booking in bookings
        if booking["student_id"] == user_id
        or booking["tutor_id"] == user_id
    ]


# ============================================================
# CONFIRM BOOKING
# ============================================================

@app.post("/bookings/{booking_id}/confirm")
def confirm_booking(booking_id: int):

    for booking in bookings:

        if booking["id"] == booking_id:

            if booking["status"] != "pending":
                raise HTTPException(
                    status_code=400,
                    detail="Booking cannot be confirmed"
                )

            booking["status"] = "confirmed"

            return {
                "message": "Booking confirmed",
                "booking": booking
            }

    raise HTTPException(
        status_code=404,
        detail="Booking not found"
    )


# ============================================================
# COMPLETE SESSION
# ============================================================

@app.post("/bookings/{booking_id}/complete")
def complete_session(booking_id: int):

    for booking in bookings:

        if booking["id"] == booking_id:

            if booking["status"] != "confirmed":
                raise HTTPException(
                    status_code=400,
                    detail="Booking must be confirmed first"
                )

            tutor = users[booking["tutor_id"]]

            # Release escrow
            tutor["credits"] += booking["credits"]

            booking["status"] = "completed"

            # Record transaction
            transactions.append({
                "user_id": tutor["id"],
                "type": "escrow_release",
                "amount": booking["credits"],
                "booking_id": booking_id,
                "timestamp": datetime.now().isoformat()
            })

            return {
                "message": "Session completed successfully",
                "credits_transferred": booking["credits"],
                "booking": booking
            }

    raise HTTPException(
        status_code=404,
        detail="Booking not found"
    )


# ============================================================
# DISPUTE API
# ============================================================

@app.post("/bookings/{booking_id}/dispute")
def create_dispute(
    booking_id: int,
    dispute: DisputeCreate
):

    for booking in bookings:

        if booking["id"] == booking_id:

            if booking["status"] == "completed":

                raise HTTPException(
                    status_code=400,
                    detail="Cannot dispute a completed session"
                )

            new_dispute = {
                "booking_id": booking_id,
                "reason": dispute.reason,
                "status": "open",
                "created_at": datetime.now().isoformat()
            }

            disputes.append(new_dispute)

            booking["status"] = "disputed"

            return {
                "message": "Dispute submitted successfully",
                "dispute": new_dispute
            }

    raise HTTPException(
        status_code=404,
        detail="Booking not found"
    )


# ============================================================
# RATING API
# ============================================================

@app.post("/bookings/{booking_id}/rating")
def rate_tutor(
    booking_id: int,
    rating: RatingCreate
):

    if rating.rating < 1 or rating.rating > 5:

        raise HTTPException(
            status_code=400,
            detail="Rating must be between 1 and 5"
        )

    for booking in bookings:

        if booking["id"] == booking_id:

            if booking["status"] != "completed":

                raise HTTPException(
                    status_code=400,
                    detail="Session must be completed first"
                )

            tutor = users[booking["tutor_id"]]

            old_rating = tutor["rating"]
            old_count = tutor["rating_count"]

            new_count = old_count + 1

            new_rating = (
                (old_rating * old_count)
                + rating.rating
            ) / new_count

            tutor["rating"] = round(
                new_rating,
                2
            )

            tutor["rating_count"] = new_count

            ratings.append({
                "booking_id": booking_id,
                "tutor_id": tutor["id"],
                "rating": rating.rating,
                "review": rating.review
            })

            return {
                "message": "Rating submitted successfully",
                "new_tutor_rating": tutor["rating"]
            }

    raise HTTPException(
        status_code=404,
        detail="Booking not found"
    )


# ============================================================
# ANALYTICS API
# ============================================================

@app.get("/users/{user_id}/analytics")
def get_analytics(user_id: int):

    if user_id not in users:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    hours_taught = 0
    hours_received = 0

    for booking in bookings:

        if booking["status"] != "completed":
            continue

        if booking["tutor_id"] == user_id:
            hours_taught += booking["duration"]

        if booking["student_id"] == user_id:
            hours_received += booking["duration"]

    return {
        "user_id": user_id,
        "hours_taught": hours_taught,
        "hours_received": hours_received,
        "net_learning_balance":
            hours_received - hours_taught
    }



    #python -m uvicorn main:app --reload
