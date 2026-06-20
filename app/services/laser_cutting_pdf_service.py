import os
import base64
from datetime import datetime
from xml.etree import ElementTree as ET
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.part import Part
from app.models.assembly import Assembly
from app.models.uploaded_file import UploadedFile
from app.services.assembly_tree import iter_assembly_parts

# ─── Constants ────────────────────────────────────────────────────────────────

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
MIME_MAP = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
UPLOAD_ROOT = "static/uploads"
EXCLUDED_CATEGORIES = {"welding_drawing", "bending_drawing"}

_PLACEHOLDER_SVG = (
    '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">'
    '<polygon points="50,12 88,32 88,68 50,88 12,68 12,32"'
    '         fill="#f0f2f5" stroke="#c0c5cc" stroke-width="3"/>'
    '<line x1="50" y1="12" x2="50" y2="88" stroke="#d0d5dc" stroke-width="2"/>'
    '<line x1="12" y1="32" x2="88" y2="68" stroke="#d0d5dc" stroke-width="2"/>'
    '<line x1="88" y1="32" x2="12" y2="68" stroke="#d0d5dc" stroke-width="2"/>'
    '</svg>'
).encode("utf-8")
PLACEHOLDER_DATA_URI = "data:image/svg+xml;base64," + base64.b64encode(_PLACEHOLDER_SVG).decode()


def _make_file_badge_svg(label: str) -> str:
    color = {"PDF": "#dc2626", "DXF": "#2563eb"}.get(label.upper(), "#4b5563")
    svg = (
        '<svg viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">'
        '<rect x="10" y="5" width="80" height="110" rx="6"'
        '      fill="#f8fafc" stroke="#cbd5e1" stroke-width="2"/>'
        '<polygon points="60,5 90,5 90,35 60,35" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="1"/>'
        '<polygon points="60,5 90,35 60,35" fill="#cbd5e1"/>'
        f'<rect x="10" y="64" width="80" height="34" rx="4" fill="{color}"/>'
        f'<text x="50" y="87" text-anchor="middle" font-size="20" font-weight="bold"'
        f'      fill="#fff" font-family="Arial,sans-serif">{label}</text>'
        '</svg>'
    ).encode("utf-8")
    return "data:image/svg+xml;base64," + base64.b64encode(svg).decode()


# ─── Preview renderers ────────────────────────────────────────────────────────

def _render_dxf_preview(abs_path: str) -> str | None:
    """
    Render a DXF file to an SVG data URI using ezdxf's SVG backend.
    Falls back to matplotlib PNG if needed, then returns None so the caller
    can show a generic badge instead.
    """
    try:
        import ezdxf
        doc = ezdxf.readfile(abs_path)
        msp = doc.modelspace()
    except Exception:
        return None

    # ── Attempt 1: ezdxf SVG backend (no matplotlib required) ──
    try:
        from ezdxf.addons.drawing import RenderContext, Frontend, layout
        from ezdxf.addons.drawing.svg import SVGBackend
        from ezdxf.addons.drawing.properties import LayoutProperties

        ctx = RenderContext(doc)
        lp = LayoutProperties.from_layout(msp)
        lp.set_colors("#ffffff", "#000000")  # white background, black lines

        backend = SVGBackend()
        Frontend(ctx, backend).draw_layout(msp, layout_properties=lp)
        page = layout.Page(width=80, height=80, units=layout.Units.mm)
        svg = backend.get_string(page)
        if svg:
            return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    except Exception:
        pass

    # ── Attempt 2: matplotlib PNG ──
    try:
        import io
        from ezdxf.addons.drawing import RenderContext, Frontend
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig = plt.figure(figsize=(3, 3), dpi=96)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_aspect("equal")
        backend = MatplotlibBackend(ax)
        Frontend(RenderContext(doc), backend).draw_layout(msp)
        ax.set_axis_off()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=96, bbox_inches="tight",
                    facecolor="white", edgecolor="none", pad_inches=0.1)
        plt.close(fig)
        buf.seek(0)
        raw = buf.read()
        if raw:
            return "data:image/png;base64," + base64.b64encode(raw).decode()
    except Exception:
        pass

    return None


def _render_pdf_preview(abs_path: str) -> str | None:
    """Render first page of a PDF to a grayscale PNG using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(abs_path)
        if not doc.page_count:
            doc.close()
            return None
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), colorspace=fitz.csGRAY)
        png_data = pix.tobytes("png")
        doc.close()
        return "data:image/png;base64," + base64.b64encode(png_data).decode()
    except Exception:
        return None


# ─── Icon resolution ──────────────────────────────────────────────────────────

def _get_entity_icon(entity_type: str, entity_id: str, db: Session) -> str:
    files = (
        db.query(UploadedFile)
        .filter(UploadedFile.entity_type == entity_type, UploadedFile.entity_id == entity_id)
        .order_by(UploadedFile.uploaded_at)
        .all()
    )

    first_label: str | None = None
    first_dxf_path: str | None = None
    first_pdf_path: str | None = None

    for f in files:
        if f.file_category in EXCLUDED_CATEGORIES:
            continue
        ext = os.path.splitext(f.original_filename)[1].lower()

        # ── Immediate return for actual images ──
        if ext in IMAGE_EXTS:
            abs_path = os.path.join(UPLOAD_ROOT, f.stored_path)
            if os.path.exists(abs_path):
                try:
                    raw = open(abs_path, "rb").read()
                    mime = MIME_MAP.get(ext, "image/png")
                    return f"data:{mime};base64," + base64.b64encode(raw).decode()
                except OSError:
                    pass

        # ── Collect first DXF/PDF path for preview attempt ──
        if ext == ".dxf" and first_dxf_path is None:
            candidate = os.path.join(UPLOAD_ROOT, f.stored_path)
            if os.path.exists(candidate):
                first_dxf_path = candidate
        elif ext == ".pdf" and first_pdf_path is None:
            candidate = os.path.join(UPLOAD_ROOT, f.stored_path)
            if os.path.exists(candidate):
                first_pdf_path = candidate

        if first_label is None and ext in {".pdf", ".dxf"}:
            first_label = "DXF" if ext == ".dxf" else "PDF"

    # ── Try rendering a real preview ──
    if first_dxf_path:
        preview = _render_dxf_preview(first_dxf_path)
        if preview:
            return preview

    if first_pdf_path:
        preview = _render_pdf_preview(first_pdf_path)
        if preview:
            return preview

    # ── Generic badge / placeholder ──
    return _make_file_badge_svg(first_label) if first_label else PLACEHOLDER_DATA_URI


# ─── CSS ──────────────────────────────────────────────────────────────────────

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: A4 portrait; margin: 12mm; }
body { font-family: Arial, sans-serif; font-size: 10pt; color: #000; background: #fff; }

.page-title {
  text-align: center;
  font-size: 20pt;
  font-weight: 900;
  letter-spacing: 1px;
  margin-bottom: 8mm;
}

table { width: 100%; border-collapse: collapse; }

thead th {
  border: 1.5px solid #000;
  padding: 4px 6px;
  text-align: center;
  font-size: 8pt;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}

tbody td { border: 1.5px solid #000; padding: 0; }

/* ── Icon cell (rowspan=2 so it spans both sub-rows) ── */
.cell-icon {
  width: 36mm;
  text-align: center;
  vertical-align: middle;
  padding: 8px 6px;
}
.cell-icon img {
  max-width: 28mm;
  max-height: 40mm;
  object-fit: contain;
  display: block;
  margin: 0 auto;
}

/* ── Name column, top sub-row ── */
.cell-name-top {
  padding: 6px 10px 5px;
  font-size: 13pt;
  font-weight: bold;
  line-height: 1.2;
  vertical-align: middle;
  min-height: 14mm;
}

/* ── Name column, bottom sub-row ── */
.cell-name-bot {
  padding: 5px 10px;
  font-size: 8.5pt;
  color: #333;
  vertical-align: middle;
  min-height: 10mm;
}

/* ── BUC column, top sub-row ── */
.cell-buc-top {
  width: 30mm;
  text-align: center;
  vertical-align: middle;
  padding: 6px 4px;
  min-height: 14mm;
}
.buc-lbl { font-size: 8pt; font-weight: bold; }
.qty-num { font-size: 24pt; font-weight: bold; line-height: 1; display: block; }

/* ── BUC column, bottom sub-row (checkbox) ── */
.cell-buc-bot {
  width: 30mm;
  text-align: center;
  vertical-align: middle;
  padding: 8px 4px;
  min-height: 10mm;
}
.checkbox {
  width: 12mm;
  height: 12mm;
  border: 1.5px solid #000;
  display: inline-block;
}

.project-info {
  margin-bottom: 6mm;
  font-size: 10pt;
  color: #333;
}
.project-info .project-name {
  font-size: 13pt;
  font-weight: bold;
  color: #000;
}
"""

_HTML_WRAPPER = """<!DOCTYPE html>
<html lang="ro">
<head><meta charset="UTF-8"/><style>{css}</style></head>
<body>
  <h1 class="page-title">TĂIERE LASER – LISTĂ PIESE</h1>
  <table>
    <thead>
      <tr>
        <th style="width:36mm">ICON</th>
        <th>NUME / LOCAȚIE FIȘIER LASER</th>
        <th style="width:30mm">BUC</th>
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</body>
</html>"""


# ─── Row builder ──────────────────────────────────────────────────────────────

def _row(item: dict, db: Session) -> str:
    """
    Each part occupies TWO <tr> rows.
    The icon cell uses rowspan=2 so it spans both naturally — this is how the
    checkbox gets truly vertically-centred without any flex-in-table tricks.
    """
    img = _get_entity_icon(item["entity_type"], item["entity_id"], db)
    path = item["location"] or "—"
    qty = item["quantity"]
    name = item["name"]
    return (
        # Row 1: icon (spans 2) | bold name | BUC + number
        f'<tr>'
        f'  <td rowspan="2" class="cell-icon"><img src="{img}" alt=""/></td>'
        f'  <td class="cell-name-top">{name}</td>'
        f'  <td class="cell-buc-top">'
        f'    <span class="buc-lbl">BUC</span>'
        f'    <span class="qty-num">{qty}</span>'
        f'  </td>'
        f'</tr>'
        # Row 2: (icon continues) | file path | checkbox
        f'<tr>'
        f'  <td class="cell-name-bot">{path}</td>'
        f'  <td class="cell-buc-bot"><div class="checkbox"></div></td>'
        f'</tr>'
    )


# ─── Data collection ──────────────────────────────────────────────────────────

def _collect_laser_parts(product: Product, db: Session, product_qty: int = 1) -> list[dict]:
    items: list[dict] = []
    seen: dict[str, int] = {}

    def _add(part: Part, qty: int) -> None:
        if not part.requires_laser_cutting:
            return
        effective = qty * product_qty
        if part.id in seen:
            items[seen[part.id]]["quantity"] += effective
            return
        seen[part.id] = len(items)
        items.append({
            "entity_id": part.id,
            "entity_type": "part",
            "name": part.name,
            "quantity": effective,
            "location": part.drawing_location or part.file_location or "",
        })

    if product.product_parts:
        for pp in product.product_parts:
            pid = pp.get("partId")
            if pid:
                part = db.query(Part).filter(Part.id == pid).first()
                if part:
                    _add(part, pp.get("quantity", 1))
    else:
        for pid in (product.part_ids or []):
            part = db.query(Part).filter(Part.id == pid).first()
            if part:
                _add(part, part.required_quantity or 1)

    if product.product_assemblies:
        asm_qty_map = {
            a["assemblyId"]: a.get("quantity", 1)
            for a in product.product_assemblies
            if a.get("assemblyId")
        }
    else:
        asm_qty_map = {aid: 1 for aid in (product.assembly_ids or [])}

    for asm_id, asm_qty in asm_qty_map.items():
        for part, qty in iter_assembly_parts(asm_id, db, multiplier=asm_qty):
            _add(part, qty)

    return items


def _collect_project_laser_parts(project, db: Session) -> list[dict]:
    all_items: list[dict] = []
    seen: dict[str, int] = {}

    for item in (project.items or []):
        pid = item.get("productId")
        if not pid:
            continue
        product = db.query(Product).filter(Product.id == pid).first()
        if not product:
            continue
        for part_item in _collect_laser_parts(product, db, product_qty=item.get("quantity", 1)):
            if part_item["entity_id"] in seen:
                all_items[seen[part_item["entity_id"]]]["quantity"] += part_item["quantity"]
            else:
                seen[part_item["entity_id"]] = len(all_items)
                all_items.append(part_item)

    return all_items


# ─── Public entry points ──────────────────────────────────────────────────────

def generate_laser_cutting_pdf(product: Product, db: Session) -> bytes:
    from weasyprint import HTML
    items = _collect_laser_parts(product, db)
    if not items:
        return HTML(string=(
            '<!DOCTYPE html><html><body style="font-family:Arial;padding:24px;">'
            f'<h2>Tăiere Laser</h2><p style="color:#888;margin-top:12px;">'
            f'Nicio piesă marcată pentru tăiere laser în produsul &quot;{product.name}&quot;.</p>'
            '</body></html>'
        )).write_pdf()
    rows = "".join(_row(i, db) for i in items)
    return HTML(string=_HTML_WRAPPER.format(css=_CSS, rows=rows)).write_pdf()


def generate_project_laser_cutting_pdf(project, db: Session) -> bytes:
    from weasyprint import HTML
    generated_at = datetime.now().strftime("%d.%m.%Y")
    items = _collect_project_laser_parts(project, db)
    if not items:
        return HTML(string=(
            '<!DOCTYPE html><html><body style="font-family:Arial;padding:24px;">'
            f'<h2>Tăiere Laser</h2><p style="color:#888;margin-top:12px;">'
            f'Nicio piesă marcată pentru tăiere laser în proiectul &quot;{project.name}&quot;.</p>'
            '</body></html>'
        )).write_pdf()
    rows = "".join(_row(i, db) for i in items)
    project_header = (
        f'<div class="project-info">'
        f'  <div>Proiect: <span class="project-name">{project.name}</span></div>'
        f'  <div>Generat la: {generated_at}</div>'
        f'</div>'
    )
    html = _HTML_WRAPPER.replace(
        '<table>',
        f'{project_header}\n  <table>',
    )
    return HTML(string=html.format(css=_CSS, rows=rows)).write_pdf()
