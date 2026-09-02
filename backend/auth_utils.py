import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from jose import jwt

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.orm import Session

from database import get_db
from models import User, ActivityLog

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "gradious-cloud-secret-key-change-this-later")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600

security = HTTPBearer()


def create_access_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


def log_activity(
    db: Session,
    user_id: int,
    action: str,
    file_id: int = None,
    file_name: str = None,
    details: str = None
):
    try:
        activity = ActivityLog(
            user_id=user_id,
            file_id=file_id,
            action=action,
            file_name=file_name,
            details=details
        )
        db.add(activity)
        db.commit()
    except Exception as e:
        print("Failed to record activity log:", e)
        db.rollback()