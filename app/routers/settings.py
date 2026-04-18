import os
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.setting import Setting

router = APIRouter()

BRANDING_DIR = os.path.join("static", "branding")
ALLOWED_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
MAX_SIZE = 5 * 1024 * 1024  # 5 MB

KEY_HEADER = "branding_header_url"
KEY_SIGNATURE = "branding_signature_url"


def _get_setting(db: Session, key: str) -> str | None:
    row = db.query(Setting).filter(Setting.key == key).first()
    return row.value if row else None


def _set_setting(db: Session, key: str, value: str | None) -> None:
    row = db.query(Setting).filter(Setting.key == key).first()
    if row:
        row.value = value
    else:
        db.add(Setting(key=key, value=value))
    db.commit()


def _save_image(upload: UploadFile, filename: str) -> str:
    if upload.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Doar PNG/JPEG/WebP sunt acceptate")

    contents = upload.file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Fișier prea mare (max 5 MB)")

    os.makedirs(BRANDING_DIR, exist_ok=True)
    ext = os.path.splitext(upload.filename or "")[1].lower() or ".png"
    dest = os.path.join(BRANDING_DIR, filename + ext)

    # Șterge vechea variantă cu orice extensie
    for old in os.listdir(BRANDING_DIR):
        if old.startswith(filename + "."):
            os.remove(os.path.join(BRANDING_DIR, old))

    with open(dest, "wb") as f:
        f.write(contents)

    return f"/static/branding/{filename}{ext}"


def _delete_file(filename: str) -> None:
    if not os.path.isdir(BRANDING_DIR):
        return
    for f in os.listdir(BRANDING_DIR):
        if f.startswith(filename + "."):
            os.remove(os.path.join(BRANDING_DIR, f))


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/branding")
def get_branding(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return {
        "headerUrl": _get_setting(db, KEY_HEADER),
        "signatureUrl": _get_setting(db, KEY_SIGNATURE),
    }


@router.post("/branding/header")
async def upload_header(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    url = _save_image(file, "header")
    _set_setting(db, KEY_HEADER, url)
    return {"url": url}


@router.post("/branding/signature")
async def upload_signature(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    url = _save_image(file, "signature")
    _set_setting(db, KEY_SIGNATURE, url)
    return {"url": url}


@router.delete("/branding/header")
def delete_header(db: Session = Depends(get_db), _=Depends(get_current_user)):
    _delete_file("header")
    _set_setting(db, KEY_HEADER, None)
    return {"ok": True}


@router.delete("/branding/signature")
def delete_signature(db: Session = Depends(get_db), _=Depends(get_current_user)):
    _delete_file("signature")
    _set_setting(db, KEY_SIGNATURE, None)
    return {"ok": True}
