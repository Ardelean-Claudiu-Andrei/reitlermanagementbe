import os
import base64
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.part import Part
from app.models.assembly import Assembly
from app.models.uploaded_file import UploadedFile

# ─── Constants ────────────────────────────────────────────────────────────────

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
MIME_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}
FILE_LABEL_EXT = {".pdf": "PDF", ".dxf": "DXF", ".dpd": "DPD"}
UPLOAD_ROOT = "static/uploads"
EXCLUDED_CATEGORIES = {"welding_drawing", "bending_drawing"}


# ─── SVG helpers ──────────────────────────────────────────────────────────────

def _make_file_badge_svg(label: str) -> str:
    """Return an SVG data URI showing a coloured file-type badge (PDF / DXF / DPD)."""
    color_map = {"PDF": "#dc2626", "DXF": "#2563eb", "DPD": "#7c3aed"}
    color = color_map.get(label.upper(), "#4b5563")
    svg = (
        '<svg viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">'
        '<rect x="10" y="5" width="80" height="110" rx="6"'
        '      fill="#f8fafc" stroke="#cbd5e1" stroke-width="2"/>'
        '<polygon points="60,5 90,5 90,35 60,35"'
        '         fill="#e2e8f0" stroke="#cbd5e1" stroke-width="1"/>'
        '<polygon points="60,5 90,35 60,35" fill="#cbd5e1"/>'
        f'<rect x="10" y="64" width="80" height="34" rx="4" fill="{color}"/>'
        f'<text x="50" y="87" text-anchor="middle" font-size="20"'
        f'      font-weight="bold" fill="#fff" font-family="Arial,sans-serif">{label}</text>'
        '</svg>'
    ).encode("utf-8")
    return "data:image/svg+xml;base64," + base64.b64encode(svg).decode()


_PLACEHOLDER_SVG = (
    '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">'
    '<polygon points="50,12 88,32 88,68 50,88 12,68 12,32"'
    '         fill="#f0f2f5" stroke="#c0c5cc" stroke-width="3"/>'
    '<line x1="50" y1="12" x2="50" y2="88" stroke="#d0d5dc" stroke-width="2"/>'
    '<line x1="12" y1="32" x2="88" y2="68" stroke="#d0d5dc" stroke-width="2"/>'
    '<line x1="88" y1="32" x2="12" y2="68" stroke="#d0d5dc" stroke-width="2"/>'
    '<text x="50" y="97" text-anchor="middle" font-size="8"'
    '      fill="#aab" font-family="Arial,sans-serif">PIESĂ</text>'
    '</svg>'
).encode("utf-8")
PLACEHOLDER_DATA_URI = "data:image/svg+xml;base64," + base64.b64encode(_PLACEHOLDER_SVG).decode()


def _get_entity_icon(entity_type: str, entity_id: str, db: Session) -> str:
    """
    Return a data URI for the entity's icon.

    Priority:
      1. First image upload (png/jpg/jpeg/webp) from main/general uploads
         (welding_drawing and bending_drawing are always excluded)
      2. Coloured SVG badge for the first PDF / DXF / DPD upload
      3. Generic cube placeholder
    """
    files = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.entity_type == entity_type,
            UploadedFile.entity_id == entity_id,
        )
        .order_by(UploadedFile.uploaded_at)
        .all()
    )

    first_type_label: str | None = None  # fallback badge label

    for f in files:
        if f.file_category in EXCLUDED_CATEGORIES:
            continue
        ext = os.path.splitext(f.original_filename)[1].lower()

        # Priority 1 – real image
        if ext in IMAGE_EXTS:
            abs_path = os.path.join(UPLOAD_ROOT, f.stored_path)
            if not os.path.exists(abs_path):
                continue
            try:
                with open(abs_path, "rb") as fh:
                    raw = fh.read()
                mime = MIME_MAP.get(ext, "image/png")
                return f"data:{mime};base64," + base64.b64encode(raw).decode()
            except OSError:
                continue

        # Priority 2 – remember first known type for badge
        if first_type_label is None and ext in FILE_LABEL_EXT:
            first_type_label = FILE_LABEL_EXT[ext]

    if first_type_label:
        return _make_file_badge_svg(first_type_label)
    return PLACEHOLDER_DATA_URI


# ─── CSS page style ───────────────────────────────────────────────────────────

PAGE_STYLE = """
* { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: A4; margin: 12mm; }
body { font-family: Arial, sans-serif; font-size: 10pt; color: #111; }

/* Two cards per page */
.card-pair { page-break-after: always; }
.card-pair:last-child { page-break-after: avoid; }

/* ── Outer card ── */
.card {
  border: 2.5px solid #1a1a2e;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 8mm;
}

/* ── Top section: icon | details | barcode ── */
.card-top {
  display: flex;
  flex-direction: row;
  border-bottom: 2px solid #1a1a2e;
  min-height: 60mm;
}

/* Left: icon / image */
.card-icon {
  width: 52mm;
  flex-shrink: 0;
  border-right: 1.5px solid #ccc;
  background: #f7f8fa;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px;
  gap: 5px;
}
.card-icon img {
  max-width: 44mm;
  max-height: 44mm;
  object-fit: contain;
}
.icon-label {
  font-size: 7pt;
  color: #aaa;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-align: center;
}

/* Center: name + details box */
.card-center {
  flex: 1;
  padding: 8px 10px;
  border-right: 1.5px solid #ccc;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.center-top-label {
  font-size: 7pt;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.item-name {
  font-size: 13pt;
  font-weight: bold;
  color: #1a1a2e;
  line-height: 1.2;
  margin-bottom: 4px;
}
.details-box {
  border: 1.5px solid #1a1a2e;
  border-radius: 3px;
  flex: 1;
  overflow: hidden;
}
.details-header {
  background: #1a1a2e;
  color: #fff;
  font-size: 7pt;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 3px 8px;
  text-align: center;
}
.detail-row {
  border-bottom: 1px solid #eee;
  padding: 3px 8px;
  font-size: 8.5pt;
  word-break: break-word;
}
.detail-row:last-child { border-bottom: none; }
.detail-key {
  font-size: 7pt;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  display: block;
  margin-bottom: 1px;
}
.detail-val {
  font-weight: 600;
  color: #1a1a2e;
  word-break: break-all;
}

/* Right: barcode */
.card-barcode {
  width: 48mm;
  flex-shrink: 0;
  padding: 8px 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  gap: 4px;
}
.barcode-label {
  font-size: 7pt;
  color: #888;
  text-transform: uppercase;
  font-weight: bold;
  letter-spacing: 0.5px;
}
.barcode-bars {
  width: 38mm;
  height: 24mm;
  border: 1px solid #222;
  background: repeating-linear-gradient(
    90deg,
    #111 0px,  #111 2px,
    #fff 2px,  #fff 4px,
    #111 4px,  #111 5px,
    #fff 5px,  #fff 8px,
    #111 8px,  #111 9px,
    #fff 9px,  #fff 12px,
    #111 12px, #111 14px,
    #fff 14px, #fff 15px,
    #111 15px, #111 16px,
    #fff 16px, #fff 20px,
    #111 20px, #111 22px,
    #fff 22px, #fff 24px,
    #111 24px, #111 25px,
    #fff 25px, #fff 28px
  );
}
.barcode-code {
  font-family: monospace;
  font-size: 8pt;
  text-align: center;
  word-break: break-all;
  color: #222;
  max-width: 38mm;
}
.qty-badge {
  display: inline-block;
  background: #1a1a2e;
  color: #fff;
  font-size: 10pt;
  font-weight: bold;
  padding: 3px 10px;
  border-radius: 3px;
  margin-top: 4px;
}

/* ── Bottom: notes / operator confirmation area ── */
.card-notes {
  min-height: 42mm;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
  gap: 0;
}
.notes-line {
  border-bottom: 1px solid #ddd;
  flex: 1;
  min-height: 10mm;
}
"""

# ─── HTML templates ───────────────────────────────────────────────────────────

HTML_WRAPPER = """<!DOCTYPE html>
<html lang="ro">
<head>
  <meta charset="UTF-8"/>
  <style>{style}</style>
</head>
<body>
  {pairs}
</body>
</html>"""

CARD_HTML = """
<div class="card">
  <div class="card-top">
    <div class="card-icon">
      <img src="{img_src}" alt="icon"/>
      <div class="icon-label">{item_type}</div>
    </div>
    <div class="card-center">
      <div class="center-top-label">NUME</div>
      <div class="item-name">{name}</div>
      <div class="details-box">
        <div class="details-header">DETALII LASER</div>
        <div class="detail-row">
          <span class="detail-key">Cod / ID</span>
          <span class="detail-val">{code}</span>
        </div>
        <div class="detail-row">
          <span class="detail-key">Tip</span>
          <span class="detail-val">{item_type}</span>
        </div>
        <div class="detail-row">
          <span class="detail-key">Locație desen laser</span>
          <span class="detail-val">{location}</span>
        </div>
      </div>
    </div>
    <div class="card-barcode">
      <div class="barcode-label">COD DE BARE</div>
      <div class="barcode-bars"></div>
      <div class="barcode-code">{barcode_val}</div>
      <div class="qty-badge">&#215; {quantity}</div>
    </div>
  </div>
  <div class="card-notes">
    <div class="notes-line"></div>
    <div class="notes-line"></div>
    <div class="notes-line"></div>
  </div>
</div>"""


# ─── Data collection ──────────────────────────────────────────────────────────

def _collect_laser_parts(product: Product, db: Session) -> list[dict]:
    """
    Collect all parts requiring laser cutting, deduplicating by part ID
    and summing quantities across assemblies and direct-part references.

    Each returned dict has:
      entity_id, entity_type, code, name, item_type, quantity, location, barcode_val
    """
    laser_items: list[dict] = []
    seen: dict[str, int] = {}  # entity_id → index in laser_items

    def _add(part: Part, quantity: int) -> None:
        if not part.requires_laser_cutting:
            return
        if part.id in seen:
            laser_items[seen[part.id]]["quantity"] += quantity
            return
        seen[part.id] = len(laser_items)
        code = part.code or part.id[:8].upper()
        barcode_val = part.code or ("LASER-" + part.id[:8].upper())
        laser_items.append({
            "entity_id": part.id,
            "entity_type": "part",
            "code": code,
            "name": part.name,
            "item_type": "Piesă",
            "quantity": quantity,
            "location": part.drawing_location or part.file_location or "",
            "barcode_val": barcode_val,
        })

    # Direct parts attached to product
    for part_id in (product.part_ids or []):
        part = db.query(Part).filter(Part.id == part_id).first()
        if part:
            _add(part, part.required_quantity or 1)

    # Parts inside each assembly
    for assembly_id in (product.assembly_ids or []):
        assembly = db.query(Assembly).filter(Assembly.id == assembly_id).first()
        if not assembly:
            continue
        for ap in (assembly.parts or []):
            part_id = ap.get("partId")
            if not part_id:
                continue
            part = db.query(Part).filter(Part.id == part_id).first()
            if part:
                _add(part, ap.get("quantity", 1))

    return laser_items


# ─── PDF generator ────────────────────────────────────────────────────────────

def generate_laser_cutting_pdf(product: Product, db: Session) -> bytes:
    from weasyprint import HTML

    items = _collect_laser_parts(product, db)

    if not items:
        fallback = (
            '<!DOCTYPE html><html><body style="font-family:Arial;padding:24px;">'
            '<h2>Export Debitare Laser</h2>'
            f'<p style="color:#888;margin-top:12px;">Nu există piese marcate pentru debitare laser'
            f' în produsul &quot;{product.name}&quot;.</p>'
            '</body></html>'
        )
        return HTML(string=fallback).write_pdf()

    # Build one card per item
    cards: list[str] = []
    for item in items:
        img_src = _get_entity_icon(item["entity_type"], item["entity_id"], db)
        cards.append(CARD_HTML.format(
            img_src=img_src,
            item_type=item["item_type"],
            name=item["name"],
            code=item["code"],
            location=item["location"] or "—",
            quantity=item["quantity"],
            barcode_val=item["barcode_val"],
        ))

    # Pair cards into page groups (2 per A4 page)
    pairs: list[str] = []
    for i in range(0, len(cards), 2):
        c1 = cards[i]
        c2 = cards[i + 1] if i + 1 < len(cards) else ""
        pairs.append(f'<div class="card-pair">{c1}{c2}</div>')

    html = HTML_WRAPPER.format(
        style=PAGE_STYLE,
        pairs="".join(pairs),
    )
    return HTML(string=html).write_pdf()
