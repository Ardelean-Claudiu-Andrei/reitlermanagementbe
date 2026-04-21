import base64
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.branding_asset import BrandingAsset

router = APIRouter()

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
MAX_SIZE = 5 * 1024 * 1024  # 5 MB

KEY_HEADER = "header"
KEY_SIGNATURE = "signature"


def _get_asset(db: Session, key: str) -> BrandingAsset | None:
    return db.query(BrandingAsset).filter(BrandingAsset.key == key).first()


def _save_asset(db: Session, key: str, upload: UploadFile) -> None:
    if upload.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Doar PNG/JPEG/WebP sunt acceptate")

    data = upload.file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Fișier prea mare (max 5 MB)")

    row = db.query(BrandingAsset).filter(BrandingAsset.key == key).first()
    if row:
        row.data = data
        row.content_type = upload.content_type
    else:
        db.add(BrandingAsset(key=key, data=data, content_type=upload.content_type))
    db.commit()


def get_asset_data_uri(db: Session, key: str) -> str | None:
    """Return a base64 data URI for the asset, or None if not set."""
    row = _get_asset(db, key)
    if not row or not row.data:
        return None
    b64 = base64.b64encode(row.data).decode()
    return f"data:{row.content_type};base64,{b64}"


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/branding")
def get_branding(db: Session = Depends(get_db), _=Depends(get_current_user)):
    header = _get_asset(db, KEY_HEADER)
    signature = _get_asset(db, KEY_SIGNATURE)
    return {
        "headerUrl": "/api/settings/branding/header/image" if (header and header.data) else None,
        "signatureUrl": "/api/settings/branding/signature/image" if (signature and signature.data) else None,
    }


@router.get("/branding/header/image")
def get_header_image(db: Session = Depends(get_db)):
    row = _get_asset(db, KEY_HEADER)
    if not row or not row.data:
        raise HTTPException(status_code=404, detail="Header image not found")
    return Response(content=row.data, media_type=row.content_type)


@router.get("/branding/signature/image")
def get_signature_image(db: Session = Depends(get_db)):
    row = _get_asset(db, KEY_SIGNATURE)
    if not row or not row.data:
        raise HTTPException(status_code=404, detail="Signature image not found")
    return Response(content=row.data, media_type=row.content_type)


@router.post("/branding/header")
async def upload_header(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    _save_asset(db, KEY_HEADER, file)
    return {"url": "/api/settings/branding/header/image"}


@router.post("/branding/signature")
async def upload_signature(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    _save_asset(db, KEY_SIGNATURE, file)
    return {"url": "/api/settings/branding/signature/image"}


@router.delete("/branding/header")
def delete_header(db: Session = Depends(get_db), _=Depends(get_current_user)):
    row = _get_asset(db, KEY_HEADER)
    if row:
        db.delete(row)
        db.commit()
    return {"ok": True}


@router.delete("/branding/signature")
def delete_signature(db: Session = Depends(get_db), _=Depends(get_current_user)):
    row = _get_asset(db, KEY_SIGNATURE)
    if row:
        db.delete(row)
        db.commit()
    return {"ok": True}
