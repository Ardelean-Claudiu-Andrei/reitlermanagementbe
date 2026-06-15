import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.uploaded_file import UploadedFile

router = APIRouter()

ALLOWED_ENTITY_TYPES = {"assembly", "part", "product"}
ALLOWED_FILE_CATEGORIES = {"dxf", "pdf", "image", "welding_drawing", "bending_drawing"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
UPLOAD_ROOT = "static/uploads"


def uploaded_file_to_dict(f: UploadedFile) -> dict:
    return {
        "id": f.id,
        "entityType": f.entity_type,
        "entityId": f.entity_id,
        "fileCategory": f.file_category,
        "originalFilename": f.original_filename,
        "storedPath": f.stored_path,
        "url": f"/static/uploads/{f.stored_path}",
        "contentType": f.content_type,
        "uploadedAt": f.uploaded_at.isoformat() if f.uploaded_at else None,
    }


@router.post("/{entity_type}/{entity_id}", status_code=status.HTTP_201_CREATED)
async def upload_file(
    entity_type: str,
    entity_id: str,
    file_category: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if entity_type not in ALLOWED_ENTITY_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid entity_type. Must be one of: {', '.join(ALLOWED_ENTITY_TYPES)}")
    if file_category not in ALLOWED_FILE_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid file_category. Must be one of: {', '.join(ALLOWED_FILE_CATEGORIES)}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 50 MB)")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename or "")[1].lower()
    stored_filename = f"{file_id}{ext}"
    relative_dir = f"{entity_type}/{entity_id}"
    abs_dir = os.path.join(UPLOAD_ROOT, relative_dir)
    os.makedirs(abs_dir, exist_ok=True)

    abs_path = os.path.join(abs_dir, stored_filename)
    with open(abs_path, "wb") as fh:
        fh.write(content)

    relative_stored_path = f"{relative_dir}/{stored_filename}"

    record = UploadedFile(
        id=file_id,
        entity_type=entity_type,
        entity_id=entity_id,
        file_category=file_category,
        original_filename=file.filename or stored_filename,
        stored_path=relative_stored_path,
        content_type=file.content_type,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return uploaded_file_to_dict(record)


@router.get("/{entity_type}/{entity_id}")
def list_uploads(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if entity_type not in ALLOWED_ENTITY_TYPES:
        raise HTTPException(status_code=400, detail="Invalid entity_type")
    files = (
        db.query(UploadedFile)
        .filter(UploadedFile.entity_type == entity_type, UploadedFile.entity_id == entity_id)
        .order_by(UploadedFile.uploaded_at)
        .all()
    )
    return [uploaded_file_to_dict(f) for f in files]


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_upload(
    file_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    abs_path = os.path.join(UPLOAD_ROOT, record.stored_path)
    if os.path.exists(abs_path):
        os.remove(abs_path)

    db.delete(record)
    db.commit()
