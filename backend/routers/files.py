import os
import uuid
import json
from typing import Optional
from pathlib import Path
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, Form, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from jose import jwt

from database import get_db
from models import File, Folder, FileShare, AIAnalysis, User
from schemas import ShareRequest, FileRename, FileMove
from auth_utils import get_current_user, log_activity, SECRET_KEY, ALGORITHM
from ai_analysis import analyze_file

router = APIRouter(prefix="/files", tags=["Files"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal vulnerabilities."""
    if not filename:
        return "unnamed_file"
    # Remove any directory path components
    clean_name = os.path.basename(filename.replace("\\", "/"))
    # Remove illegal characters for Windows/Linux filesystems
    clean_name = "".join(c for c in clean_name if c not in '<>:"/\\|?*\0').strip()
    return clean_name if clean_name else "unnamed_file"


def format_file_dict(file: File, db: Session):
    ai = db.query(AIAnalysis).filter(AIAnalysis.file_id == file.id).first()
    share = db.query(FileShare).filter(FileShare.file_id == file.id, FileShare.is_active == 1).first()

    ai_dict = None
    if ai:
        ai_dict = {
            "summary": ai.summary,
            "description": ai.description,
            "tags": ai.tags,
            "insights": ai.insights,
            "created_at": ai.created_at
        }

    return {
        "id": file.id,
        "user_id": file.user_id,
        "folder_id": file.folder_id,
        "original_name": file.original_name,
        "stored_name": file.stored_name,
        "file_path": file.file_path,
        "file_size": file.file_size,
        "file_type": file.file_type,
        "uploaded_at": file.uploaded_at,
        "ai_analysis": ai_dict,
        "share_token": share.share_token if share else None
    }


@router.get("/")
@router.get("")
def get_user_files(
    q: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(File).filter(File.user_id == current_user.id)
    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.filter(File.original_name.ilike(search_term))

    files = query.order_by(File.uploaded_at.desc()).all()
    return [format_file_dict(f, db) for f in files]


@router.get("/storage")
def get_storage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    files = db.query(File).filter(File.user_id == current_user.id).all()
    total_files = len(files)
    total_bytes = sum(f.file_size or 0 for f in files)
    total_mb = round(total_bytes / (1024 * 1024), 2)

    doc_bytes = 0
    img_bytes = 0
    video_bytes = 0
    audio_bytes = 0
    code_bytes = 0
    other_bytes = 0

    for f in files:
        ftype = (f.file_type or "").lower()
        fname = (f.original_name or "").lower()
        fsize = f.file_size or 0

        if any(ext in fname for ext in [".pdf", ".doc", ".docx", ".txt", ".csv", ".json", ".md"]) or any(t in ftype for t in ["pdf", "word", "text", "csv", "json"]):
            doc_bytes += fsize
        elif any(ext in fname for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"]) or "image" in ftype:
            img_bytes += fsize
        elif any(ext in fname for ext in [".mp4", ".mov", ".avi", ".mkv", ".webm"]) or "video" in ftype:
            video_bytes += fsize
        elif any(ext in fname for ext in [".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg"]) or "audio" in ftype:
            audio_bytes += fsize
        elif any(ext in fname for ext in [".py", ".js", ".jsx", ".java", ".c", ".cpp", ".h", ".html", ".css", ".sql"]):
            code_bytes += fsize
        else:
            other_bytes += fsize

    return {
        "total_files": total_files,
        "total_storage_bytes": total_bytes,
        "total_storage_mb": total_mb,
        "categories": {
            "documents": doc_bytes,
            "images": img_bytes,
            "videos": video_bytes,
            "audio": audio_bytes,
            "code": code_bytes,
            "other": other_bytes
        }
    }


@router.get("/my-shares")
def get_my_shares(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    shares = db.query(FileShare, File).join(File, FileShare.file_id == File.id).filter(
        FileShare.user_id == current_user.id,
        FileShare.is_active == 1
    ).order_by(FileShare.created_at.desc()).all()

    results = []
    for share, file_rec in shares:
        results.append({
            "share_id": share.id,
            "share_token": share.share_token,
            "share_type": share.share_type,
            "shared_with_email": share.shared_with_email,
            "created_at": share.created_at,
            "file_id": file_rec.id,
            "original_name": file_rec.original_name,
            "file_type": file_rec.file_type,
            "file_size": file_rec.file_size,
            "share_url": f"http://127.0.0.1:8000/files/share/{share.share_token}"
        })
    return results


@router.get("/shared-with-me")
def get_shared_with_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    shares = db.query(FileShare, File, User).join(
        File, FileShare.file_id == File.id
    ).join(
        User, FileShare.user_id == User.id
    ).filter(
        FileShare.share_type == "user",
        FileShare.shared_with_email == current_user.email,
        FileShare.is_active == 1
    ).order_by(FileShare.created_at.desc()).all()

    results = []
    for share, file_rec, owner in shares:
        results.append({
            "share_id": share.id,
            "share_token": share.share_token,
            "created_at": share.created_at,
            "shared_by_name": owner.name,
            "shared_by_email": owner.email,
            "file_id": file_rec.id,
            "original_name": file_rec.original_name,
            "file_type": file_rec.file_type,
            "file_size": file_rec.file_size,
            "share_url": f"http://127.0.0.1:8000/files/share/{share.share_token}"
        })
    return results


@router.get("/folder/{folder_id}")
def get_files_by_folder(
    folder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify folder ownership
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == current_user.id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found or access denied")

    files = db.query(File).filter(
        File.user_id == current_user.id,
        File.folder_id == folder_id
    ).order_by(File.uploaded_at.desc()).all()

    return [format_file_dict(f, db) for f in files]


@router.post("/upload")
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    folder_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    original_name = sanitize_filename(file.filename)

    # If target folder specified, verify ownership
    target_folder_id = None
    if folder_id and folder_id > 0:
        folder_rec = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == current_user.id).first()
        if not folder_rec:
            raise HTTPException(status_code=404, detail="Target folder not found or access denied")
        target_folder_id = folder_rec.id

    file_ext = Path(original_name).suffix
    unique_stored_name = f"{uuid.uuid4().hex}{file_ext}"
    file_save_path = UPLOAD_DIR / unique_stored_name

    contents = await file.read()
    file_size = len(contents)

    with open(file_save_path, "wb") as f:
        f.write(contents)

    file_record = File(
        user_id=current_user.id,
        folder_id=target_folder_id,
        original_name=original_name,
        stored_name=unique_stored_name,
        file_path=str(file_save_path),
        file_size=file_size,
        file_type=file.content_type or "application/octet-stream"
    )

    db.add(file_record)
    db.commit()
    db.refresh(file_record)

    # Record upload activity
    log_activity(
        db,
        user_id=current_user.id,
        action="UPLOAD",
        file_id=file_record.id,
        file_name=original_name,
        details=f"Uploaded file ({file_size} bytes)"
    )

    # Perform AI Analysis safely
    ai_result = None
    try:
        analysis_data = analyze_file(
            file_path=str(file_save_path),
            file_name=original_name,
            file_type=file.content_type
        )

        ai_record = AIAnalysis(
            file_id=file_record.id,
            summary=analysis_data.get("summary", ""),
            description=analysis_data.get("description", ""),
            tags=str(analysis_data.get("tags", "[]")),
            insights=analysis_data.get("insights", "")
        )
        db.add(ai_record)
        db.commit()
        db.refresh(ai_record)

        ai_result = {
            "summary": ai_record.summary,
            "description": ai_record.description,
            "tags": ai_record.tags,
            "insights": ai_record.insights
        }

    except Exception as e:
        print("Error during AI analysis:", e)
        ai_result = {
            "summary": "AI analysis could not be completed at this time.",
            "description": "You can retry later.",
            "tags": "[]",
            "insights": ""
        }

    return {
        "message": "File uploaded successfully",
        "file_id": file_record.id,
        "file_name": file_record.original_name,
        "file_type": file_record.file_type,
        "file_size": file_record.file_size,
        "uploaded_at": file_record.uploaded_at,
        "ai_analysis": ai_result
    }


@router.get("/{file_id}/download")
def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Owner or authorized recipient check
    file_record = db.query(File).filter(File.id == file_id).first()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Check permission
    is_owner = (file_record.user_id == current_user.id)
    is_shared = False
    if not is_owner:
        shared_entry = db.query(FileShare).filter(
            FileShare.file_id == file_id,
            FileShare.share_type == "user",
            FileShare.shared_with_email == current_user.email,
            FileShare.is_active == 1
        ).first()
        if shared_entry:
            is_shared = True

    if not is_owner and not is_shared:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You do not have permission to download this file."
        )

    if not os.path.exists(file_record.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical file not found on server"
        )

    log_activity(
        db,
        user_id=current_user.id,
        action="DOWNLOAD",
        file_id=file_record.id,
        file_name=file_record.original_name,
        details="File downloaded"
    )

    return FileResponse(
        path=file_record.file_path,
        filename=file_record.original_name,
        media_type=file_record.file_type or "application/octet-stream"
    )


@router.get("/{file_id}/ai-analysis")
def get_ai_analysis(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(File).filter(File.id == file_id).first()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    is_owner = (file_record.user_id == current_user.id)
    is_shared = False
    if not is_owner:
        shared_entry = db.query(FileShare).filter(
            FileShare.file_id == file_id,
            FileShare.share_type == "user",
            FileShare.shared_with_email == current_user.email,
            FileShare.is_active == 1
        ).first()
        if shared_entry:
            is_shared = True

    if not is_owner and not is_shared:
        raise HTTPException(status_code=403, detail="Access denied")

    analysis = db.query(AIAnalysis).filter(AIAnalysis.file_id == file_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="AI analysis not found for this file")

    log_activity(
        db,
        user_id=current_user.id,
        action="VIEW",
        file_id=file_record.id,
        file_name=file_record.original_name,
        details="Viewed file details & AI analysis"
    )

    return {
        "id": analysis.id,
        "file_id": analysis.file_id,
        "summary": analysis.summary,
        "description": analysis.description,
        "tags": analysis.tags,
        "insights": analysis.insights,
        "created_at": analysis.created_at
    }


@router.put("/{file_id}/rename")
@router.put("/{file_id}")
def rename_file(
    file_id: int,
    payload: FileRename,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    clean_name = sanitize_filename(payload.new_name)
    if not clean_name:
        raise HTTPException(status_code=400, detail="Invalid new filename")

    file_record = db.query(File).filter(
        File.id == file_id,
        File.user_id == current_user.id
    ).first()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    old_name = file_record.original_name
    file_record.original_name = clean_name
    db.commit()

    log_activity(
        db,
        user_id=current_user.id,
        action="RENAME",
        file_id=file_record.id,
        file_name=clean_name,
        details=f"Renamed from '{old_name}' to '{clean_name}'"
    )

    return {
        "message": "File renamed successfully",
        "id": file_record.id,
        "original_name": file_record.original_name
    }


@router.put("/{file_id}/move")
def move_file(
    file_id: int,
    payload: FileMove,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(File).filter(
        File.id == file_id,
        File.user_id == current_user.id
    ).first()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    target_folder_id = None
    if payload.folder_id and payload.folder_id > 0:
        target_folder = db.query(Folder).filter(
            Folder.id == payload.folder_id,
            Folder.user_id == current_user.id
        ).first()
        if not target_folder:
            raise HTTPException(status_code=404, detail="Target folder not found or access denied")
        target_folder_id = target_folder.id

    file_record.folder_id = target_folder_id
    db.commit()

    log_activity(
        db,
        user_id=current_user.id,
        action="MOVE",
        file_id=file_record.id,
        file_name=file_record.original_name,
        details=f"Moved to folder_id={target_folder_id or 'Root'}"
    )

    return {
        "message": "File moved successfully",
        "id": file_record.id,
        "folder_id": file_record.folder_id
    }


@router.post("/{file_id}/share")
def create_share_link(
    file_id: int,
    payload: Optional[ShareRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(File).filter(
        File.id == file_id,
        File.user_id == current_user.id
    ).first()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    share_type = (payload.share_type if payload else "public").lower()
    if share_type not in ["public", "user"]:
        share_type = "public"

    target_email = None
    if share_type == "user":
        if not payload or not payload.shared_with_email or not payload.shared_with_email.strip():
            raise HTTPException(
                status_code=400,
                detail="Please specify the recipient email address for user-specific sharing."
            )
        target_email = payload.shared_with_email.strip().lower()

        if target_email == current_user.email.lower():
            raise HTTPException(
                status_code=400,
                detail="You cannot share a file with your own email address."
            )

        target_user = db.query(User).filter(User.email == target_email).first()
        if not target_user:
            raise HTTPException(
                status_code=404,
                detail=f"User with email '{target_email}' is not registered on CloudVault."
            )

    # Check for existing share
    existing_share = db.query(FileShare).filter(
        FileShare.file_id == file_id,
        FileShare.user_id == current_user.id,
        FileShare.share_type == share_type,
        FileShare.shared_with_email == target_email,
        FileShare.is_active == 1
    ).first()

    if existing_share:
        share_token = existing_share.share_token
    else:
        share_token = uuid.uuid4().hex
        share = FileShare(
            file_id=file_id,
            user_id=current_user.id,
            share_token=share_token,
            share_type=share_type,
            shared_with_email=target_email,
            is_active=1
        )
        db.add(share)
        db.commit()

    log_activity(
        db,
        user_id=current_user.id,
        action="SHARE",
        file_id=file_record.id,
        file_name=file_record.original_name,
        details=f"Shared as {share_type} (Target: {target_email or 'Anyone'})"
    )

    return {
        "message": "Share link generated successfully",
        "share_token": share_token,
        "share_type": share_type,
        "shared_with_email": target_email,
        "share_url": f"http://127.0.0.1:8000/files/share/{share_token}"
    }


@router.get("/share/{token}")
def get_shared_file(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    share = db.query(FileShare).filter(
        FileShare.share_token == token,
        FileShare.is_active == 1
    ).first()

    if not share:
        raise HTTPException(status_code=404, detail="Invalid or revoked share link")

    file_record = db.query(File).filter(File.id == share.file_id).first()
    if not file_record or not os.path.exists(file_record.file_path):
        raise HTTPException(status_code=404, detail="Shared file not found on server")

    # If share_type is specific user, enforce target email verification
    if share.share_type == "user" and share.shared_with_email:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted. This file link was shared specifically with '{share.shared_with_email}'. Please log in with that account."
            )

        token_str = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token_str, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            req_user = db.query(User).filter(User.id == int(user_id)).first()
            if not req_user or (req_user.email.lower() != share.shared_with_email.lower() and req_user.id != share.user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. This file link was shared specifically with '{share.shared_with_email}'."
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Invalid session. File is shared specifically with '{share.shared_with_email}'."
            )

    log_activity(
        db,
        user_id=share.user_id,
        action="SHARE_ACCESS",
        file_id=file_record.id,
        file_name=file_record.original_name,
        details=f"Shared file accessed via link token {token[:8]}..."
    )

    return FileResponse(
        path=file_record.file_path,
        filename=file_record.original_name,
        media_type=file_record.file_type or "application/octet-stream"
    )


@router.delete("/share/{token}")
def revoke_share_link(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    share = db.query(FileShare).filter(
        FileShare.share_token == token,
        FileShare.user_id == current_user.id
    ).first()

    if not share:
        raise HTTPException(status_code=404, detail="Share link not found or already revoked")

    file_rec = db.query(File).filter(File.id == share.file_id).first()
    file_name = file_rec.original_name if file_rec else "File"

    db.delete(share)
    db.commit()

    log_activity(
        db,
        user_id=current_user.id,
        action="SHARE_REVOKE",
        file_id=share.file_id,
        file_name=file_name,
        details="Share link revoked"
    )

    return {"message": "Share link revoked successfully"}


@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(File).filter(
        File.id == file_id,
        File.user_id == current_user.id
    ).first()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    file_name = file_record.original_name

    # Delete related AI analysis & shares
    db.query(AIAnalysis).filter(AIAnalysis.file_id == file_id).delete()
    db.query(FileShare).filter(FileShare.file_id == file_id).delete()

    # Remove file on disk if exists
    if os.path.exists(file_record.file_path):
        try:
            os.remove(file_record.file_path)
        except Exception:
            pass

    db.delete(file_record)
    db.commit()

    log_activity(
        db,
        user_id=current_user.id,
        action="DELETE",
        file_id=file_id,
        file_name=file_name,
        details=f"Deleted file '{file_name}'"
    )

    return {"message": "File deleted successfully"}
