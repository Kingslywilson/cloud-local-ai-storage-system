from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Folder, File, User
from schemas import FolderCreate, FolderRename
from auth_utils import get_current_user, log_activity

router = APIRouter(prefix="/folders", tags=["Folders"])


@router.get("/")
@router.get("")
def get_folders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    folders = db.query(Folder).filter(Folder.user_id == current_user.id).order_by(Folder.name.asc()).all()
    return [
        {
            "id": folder.id,
            "name": folder.name,
            "created_at": folder.created_at,
            "user_id": folder.user_id
        }
        for folder in folders
    ]


@router.post("/")
@router.post("")
def create_folder(
    payload: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    clean_name = payload.name.strip()
    if not clean_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Folder name cannot be empty"
        )

    existing = db.query(Folder).filter(
        Folder.user_id == current_user.id,
        Folder.name == clean_name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A folder named '{clean_name}' already exists."
        )

    folder = Folder(
        name=clean_name,
        user_id=current_user.id
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)

    log_activity(
        db,
        user_id=current_user.id,
        action="FOLDER_CREATE",
        details=f"Created folder '{clean_name}'"
    )

    return {
        "id": folder.id,
        "name": folder.name,
        "created_at": folder.created_at,
        "user_id": folder.user_id
    }


@router.put("/{folder_id}/rename")
@router.put("/{folder_id}")
def rename_folder(
    folder_id: int,
    payload: FolderRename,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    clean_name = payload.new_name.strip()
    if not clean_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New folder name cannot be empty"
        )

    folder = db.query(Folder).filter(
        Folder.id == folder_id,
        Folder.user_id == current_user.id
    ).first()

    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found or access denied"
        )

    existing = db.query(Folder).filter(
        Folder.user_id == current_user.id,
        Folder.name == clean_name,
        Folder.id != folder_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A folder named '{clean_name}' already exists."
        )

    old_name = folder.name
    folder.name = clean_name
    db.commit()

    log_activity(
        db,
        user_id=current_user.id,
        action="FOLDER_RENAME",
        details=f"Renamed folder from '{old_name}' to '{clean_name}'"
    )

    return {
        "message": "Folder renamed successfully",
        "id": folder.id,
        "name": folder.name
    }


@router.delete("/{folder_id}")
def delete_folder(
    folder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    folder = db.query(Folder).filter(
        Folder.id == folder_id,
        Folder.user_id == current_user.id
    ).first()

    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found or access denied"
        )

    folder_name = folder.name

    # Unassign files inside this folder (move to root storage)
    db.query(File).filter(
        File.folder_id == folder_id,
        File.user_id == current_user.id
    ).update({"folder_id": None})

    db.delete(folder)
    db.commit()

    log_activity(
        db,
        user_id=current_user.id,
        action="FOLDER_DELETE",
        details=f"Deleted folder '{folder_name}'"
    )

    return {"message": f"Folder '{folder_name}' deleted successfully"}

