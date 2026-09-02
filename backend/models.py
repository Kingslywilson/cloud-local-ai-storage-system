from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    DateTime,
    ForeignKey,
    func
)
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    name = Column(String(255), nullable=False)
    created_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    folder_id = Column(
        Integer,
        ForeignKey("folders.id"),
        nullable=True
    )

    original_name = Column(
        String(255),
        nullable=False
    )

    stored_name = Column(
        String(255),
        nullable=False
    )

    file_path = Column(
        String(500),
        nullable=False
    )

    file_size = Column(
        BigInteger,
        nullable=False
    )

    file_type = Column(
        String(100),
        nullable=True
    )

    uploaded_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

class FileShare(Base):
    __tablename__ = "file_shares"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    file_id = Column(
        Integer,
        ForeignKey("files.id"),
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    share_token = Column(
        String(255),
        unique=True,
        nullable=False
    )

    share_type = Column(
        String(50),
        default="public",
        nullable=False
    )

    shared_with_email = Column(
        String(150),
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

    expires_at = Column(
        DateTime,
        nullable=True
    )

    is_active = Column(
        Integer,
        default=1,
        nullable=False
    )

class AIAnalysis(Base):
    __tablename__ = "ai_analysis"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    file_id = Column(
        Integer,
        ForeignKey("files.id"),
        nullable=False
    )

    summary = Column(
        String(2000),
        nullable=True
    )

    description = Column(
        String(2000),
        nullable=True
    )

    tags = Column(
        String(1000),
        nullable=True
    )

    insights = Column(
        String(3000),
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    file_id = Column(
        Integer,
        ForeignKey("files.id"),
        nullable=True
    )

    action = Column(
        String(50),
        nullable=False
    )

    file_name = Column(
        String(255),
        nullable=True
    )

    details = Column(
        String(500),
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )