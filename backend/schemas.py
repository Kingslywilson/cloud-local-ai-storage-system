from typing import Optional
from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class FileRename(BaseModel):
    new_name: str


class FileMove(BaseModel):
    folder_id: Optional[int] = None


class FolderCreate(BaseModel):
    name: str


class FolderRename(BaseModel):
    new_name: str


class ShareRequest(BaseModel):
    share_type: str = "public"  # "public" or "user"
    shared_with_email: Optional[str] = None
