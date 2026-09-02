import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, ActivityLog
from schemas import UserRegister, UserLogin
from auth_utils import create_access_token, get_current_user, log_activity

router = APIRouter(tags=["Auth"])


@router.post("/auth/register")
@router.post("/auth/register/")
def register_user(payload: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(payload.password.encode("utf-8"), salt).decode("utf-8")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_activity(db, user.id, "REGISTER", details=f"User registered with email {user.email}")

    access_token = create_access_token(user_id=user.id)

    return {
        "message": "User registered successfully",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }


@router.post("/auth/login")
@router.post("/auth/login/")
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not bcrypt.checkpw(payload.password.encode("utf-8"), user.password_hash.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    log_activity(db, user.id, "LOGIN", details="User logged in successfully")

    access_token = create_access_token(user_id=user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }


@router.post("/auth/logout")
@router.post("/auth/logout/")
def logout_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    log_activity(db, current_user.id, "LOGOUT", details="User logged out")
    return {"message": "Logged out successfully"}


@router.get("/auth/me")
@router.get("/auth/me/")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "created_at": current_user.created_at
    }


@router.get("/activity")
@router.get("/activity/")
def get_user_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    activities = db.query(ActivityLog).filter(
        ActivityLog.user_id == current_user.id
    ).order_by(ActivityLog.created_at.desc()).all()

    return [
        {
            "id": act.id,
            "user_id": act.user_id,
            "file_id": act.file_id,
            "action": act.action,
            "file_name": act.file_name,
            "details": act.details,
            "created_at": act.created_at
        }
        for act in activities
    ]

