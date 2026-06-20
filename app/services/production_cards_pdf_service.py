"""
Production cards PDF service.

Generates one card per entity in the project hierarchy:
  Product → Assemblies (each with their Parts) → direct Parts of the Product.

Each card: icon | name / project ref / barcode | steps with checkboxes | notes.
2 cards per A4 page, black-and-white, print-friendly.
"""

import os
import base64
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.assembly import Assembly
from app.models.part import Part
from app.models.uploaded_file import UploadedFile
from app.services.assembly_tree import iter_assembly_nodes

# ─── Icon helpers ─────────────────────────────────────────────────────────────

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
_MIME_MAP = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
_FILE_LABEL_EXT = {".pdf": "PDF", ".dxf": "DXF"}
_UPLOAD_ROOT = "static/uploads"
_EXCLUDED_CATS = {"welding_drawing", "bending_drawing"}

_PLACEHOLDER_SVG = (
    '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">'
    '<rect x="5" y="5" width="90" height="90" rx="6" fill="#f5f5f5" stroke="#bbb" stroke-width="2"/>'
    '<line x1="15" y1="15" x2="85" y2="85" stroke="#ddd" stroke-width="2"/>'
    '<line x1="85" y1="15" x2="15" y2="85" stroke="#ddd" stroke-width="2"/>'
    '<rect x="30" y="30" width="40" height="40" rx="3" fill="none" stroke="#ccc" stroke-width="2"/>'
    '</svg>'
).encode()
_PLACEHOLDER_URI = "data:image/svg+xml;base64," + base64.b64encode(_PLACEHOLDER_SVG).decode()


def _make_file_badge(label: str) -> str:
    color = {"PDF": "#dc2626", "DXF": "#2563eb"}.get(label.upper(), "#555")
    svg = (
        '<svg viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">'
        '<rect x="10" y="5" width="80" height="110" rx="6" fill="#f8fafc" stroke="#cbd5e1" stroke-width="2"/>'
        '<polygon points="60,5 90,5 90,35 60,35" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="1"/>'
        '<polygon points="60,5 90,35 60,35" fill="#cbd5e1"/>'
        f'<rect x="10" y="64" width="80" height="34" rx="4" fill="{color}"/>'
        f'<text x="50" y="87" text-anchor="middle" font-size="20" font-weight="bold"'
        f'      fill="#fff" font-family="Arial,sans-serif">{label}</text>'
        '</svg>'
    ).encode()
    return "data:image/svg+xml;base64," + base64.b64encode(svg).decode()


def _render_dxf_preview(abs_path: str) -> str | None:
    try:
        import ezdxf
        doc = ezdxf.readfile(abs_path)
        msp = doc.modelspace()
    except Exception:
        return None

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


def _icon(entity_type: str, entity_id: str, db: Session) -> str:
    files = (
        db.query(UploadedFile)
        .filter(UploadedFile.entity_type == entity_type, UploadedFile.entity_id == entity_id)
        .order_by(UploadedFile.uploaded_at)
        .all()
    )
    fallback_label = None
    first_dxf_path: str | None = None

    for f in files:
        if f.file_category in _EXCLUDED_CATS:
            continue
        ext = os.path.splitext(f.original_filename)[1].lower()
        if ext in _IMAGE_EXTS:
            path = os.path.join(_UPLOAD_ROOT, f.stored_path)
            if os.path.exists(path):
                try:
                    raw = open(path, "rb").read()
                    return f"data:{_MIME_MAP.get(ext, 'image/png')};base64," + base64.b64encode(raw).decode()
                except OSError:
                    pass
        if ext == ".dxf" and first_dxf_path is None:
            path = os.path.join(_UPLOAD_ROOT, f.stored_path)
            if os.path.exists(path):
                first_dxf_path = path
        if fallback_label is None and ext in _FILE_LABEL_EXT:
            fallback_label = _FILE_LABEL_EXT[ext]

    if first_dxf_path:
        preview = _render_dxf_preview(first_dxf_path)
        if preview:
            return preview

    return _make_file_badge(fallback_label) if fallback_label else _PLACEHOLDER_URI


# ─── CSS ──────────────────────────────────────────────────────────────────────

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: A4; margin: 10mm; }
body { font-family: Arial, sans-serif; font-size: 10pt; color: #000; background: #fff; }

.card-pair {
  page-break-after: always;
  height: 277mm;
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
}
.card-pair:last-child { page-break-after: avoid; }

/* ── Card shell ── */
.card {
  border: 2px solid #000;
  display: flex;
  flex-direction: column;
  flex: 0 1 132mm;
  overflow: hidden;
}

/* ── Header row: icon | info ── */
.card-top {
  display: flex;
  flex-direction: row;
  border-bottom: 2px solid #000;
  min-height: 45mm;
}

.card-icon {
  width: 48mm;
  flex-shrink: 0;
  border-right: 1.5px solid #999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  background: #fff;
}
.card-icon img {
  max-width: 42mm;
  max-height: 40mm;
  object-fit: contain;
}

.card-info {
  flex: 1;
  position: relative;
  padding-bottom: 24mm;
  overflow: hidden;
}
.info-type {
  font-size: 6.5pt;
  color: #777;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  padding: 4px 8px 0;
}
.info-name {
  font-size: 15pt;
  font-weight: bold;
  line-height: 1.15;
  padding: 2px 8px 4px;
  border-bottom: 1px solid #ccc;
}
.info-project {
  font-size: 8pt;
  padding: 3px 8px;
  border-bottom: 1px solid #ccc;
  color: #333;
}
.info-project strong { font-weight: 700; color: #000; }
.info-barcode {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 4px 8px 5px;
}
.barcode-lbl {
  font-size: 6.5pt;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #888;
  margin-bottom: 2px;
}
.barcode-bars {
  width: 60mm;
  height: 14mm;
  margin-bottom: 2px;
  border: 1px solid #222;
  background: repeating-linear-gradient(
    90deg,
    #000 0px,  #000 2px,  #fff 2px,  #fff 4px,
    #000 4px,  #000 5px,  #fff 5px,  #fff 8px,
    #000 8px,  #000 9px,  #fff 9px,  #fff 12px,
    #000 12px, #000 14px, #fff 14px, #fff 15px,
    #000 15px, #000 16px, #fff 16px, #fff 20px,
    #000 20px, #000 22px, #fff 22px, #fff 24px,
    #000 24px, #000 25px, #fff 25px, #fff 28px
  );
}
.barcode-val {
  font-family: monospace;
  font-size: 7.5pt;
  color: #222;
  letter-spacing: 0.5px;
}

/* ── Steps ── */
.card-steps {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-bottom: 1.5px solid #000;
  min-height: 0;
}
.section-header {
  font-size: 6.5pt;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: #fff;
  background: #000;
  padding: 3px 10px;
}
.step-row {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 3px 10px;
  border-bottom: 1px solid #eee;
  min-height: 7.5mm;
}
.step-row:last-child { border-bottom: none; }
.step-cb {
  width: 11px; height: 11px;
  border: 1.5px solid #000;
  flex-shrink: 0;
  display: inline-block;
}
.step-num {
  font-size: 7.5pt; color: #999;
  flex-shrink: 0; min-width: 16px;
  font-family: monospace;
}
.step-name { font-size: 9pt; font-weight: 600; flex: 1; }
.step-type {
  font-size: 6.5pt; color: #666;
  background: #f0f0f0;
  border-radius: 2px;
  padding: 1px 4px;
  flex-shrink: 0;
}
.no-steps {
  padding: 6px 10px;
  font-size: 8pt;
  color: #bbb;
  font-style: italic;
}

/* ── Product composition summary (assemblies / direct parts) ── */
.comp-header {
  font-size: 6.5pt;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #555;
  background: #f0f0f0;
  padding: 3px 10px;
  border-top: 1px solid #ccc;
}
.comp-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-bottom: 1px solid #eee;
  min-height: 6.5mm;
}
.comp-row:last-child { border-bottom: none; }
.comp-type { font-size: 7pt; color: #666; font-weight: 600; flex-shrink: 0; }
.comp-name { font-size: 9pt; font-weight: 600; flex: 1; }

/* ── Notes ── */
.card-notes {
  flex-shrink: 0;
  min-height: 16mm;
}
.notes-body {
  height: 12mm;
}
"""

_HTML_WRAPPER = """<!DOCTYPE html>
<html lang="ro">
<head><meta charset="UTF-8"/><style>{css}</style></head>
<body>{pairs}</body>
</html>"""


# ─── Barcode payload helpers ──────────────────────────────────────────────────
# The barcode is currently a decorative CSS pattern (no real encoder). These
# helpers build the structured payload that a real barcode/QR generator would
# encode later, so scanning can resolve project/entity/step without redesign.

def build_project_item_barcode_payload(project_id: str, entity_type: str, entity_id: str, code: str) -> str:
    """PROJECT_ITEM|projectId=...|entityType=...|entityId=...|code=..."""
    return (
        f"PROJECT_ITEM|projectId={project_id}|entityType={entity_type}"
        f"|entityId={entity_id}|code={code or ''}"
    )


def build_project_step_barcode_payload(project_id: str, entity_type: str, entity_id: str, step_id: str) -> str:
    """
    PROJECT_STEP|projectId=...|entityType=...|entityId=...|stepId=...
    Only call this when step_id is a real persisted AssemblyStep.id — never invent one.
    """
    return (
        f"PROJECT_STEP|projectId={project_id}|entityType={entity_type}"
        f"|entityId={entity_id}|stepId={step_id}"
    )


# ─── Card builder ─────────────────────────────────────────────────────────────

def _steps_rows(steps: list, project_id: str, entity_type: str, entity_id: str) -> str:
    if not steps:
        return ""
    html = ""
    for i, s in enumerate(steps):
        step_id = s.get("id")
        name = s.get("name", "")
        desc = s.get("description", "")
        stype = s.get("type", "")
        display = name + (f' <span style="font-size:8pt;color:#777;font-weight:normal;">— {desc}</span>' if desc else "")
        type_badge = f'<span class="step-type">{stype}</span>' if stype else ""
        step_payload_attr = ""
        if step_id:
            payload = build_project_step_barcode_payload(project_id, entity_type, entity_id, step_id)
            step_payload_attr = f' data-step-payload="{payload}"'
        html += (
            f'<div class="step-row"{step_payload_attr}>'
            f'<span class="step-cb"></span>'
            f'<span class="step-num">{i+1}.</span>'
            f'<span class="step-name">{display}</span>'
            f'{type_badge}'
            f'</div>'
        )
    return html


def _composition_rows(items: list[dict], project_id: str) -> str:
    """Summarizes the assemblies / direct parts a Product card is made of, each checkable."""
    if not items:
        return ""
    rows = ""
    for it in items:
        payload = build_project_item_barcode_payload(project_id, it["entity_type"], it["entity_id"], it.get("code", ""))
        rows += (
            f'<div class="comp-row" data-item-payload="{payload}">'
            f'<span class="step-cb"></span>'
            f'<span class="comp-type">{it["type_label"]}:</span>'
            f'<span class="comp-name">{it["name"]}</span>'
            f'</div>'
        )
    return f'<div class="comp-header">Compoziție produs</div>{rows}'


def _card(entity_type: str, entity_id: str, name: str, code: str,
          type_label: str, steps: list, proj_code: str, proj_name: str,
          db: Session, project_id: str, composition: list[dict] | None = None) -> str:
    img = _icon(entity_type, entity_id, db)
    barcode_display = code or entity_id[:14].upper()
    payload = build_project_item_barcode_payload(project_id, entity_type, entity_id, code)

    sections = []
    steps_html = _steps_rows(steps, project_id, entity_type, entity_id)
    if steps_html:
        sections.append(steps_html)
    if composition:
        sections.append(_composition_rows(composition, project_id))
    if not sections:
        sections.append('<div class="no-steps">— Nicio etapă de producție —</div>')
    content_html = "".join(sections)

    return f"""
<div class="card">
  <div class="card-top">
    <div class="card-icon"><img src="{img}" alt=""/></div>
    <div class="card-info">
      <div class="info-type">{type_label}</div>
      <div class="info-name">{name}</div>
      <div class="info-project">Proiect: <strong>{proj_code}</strong> — {proj_name}</div>
      <div class="info-barcode">
        <div class="barcode-lbl">Cod de bare</div>
        <div class="barcode-bars" data-payload="{payload}"></div>
        <div class="barcode-val">{barcode_display}</div>
      </div>
    </div>
  </div>
  <div class="card-steps">
    <div class="section-header">Pași de producție</div>
    {content_html}
  </div>
  <div class="card-notes">
    <div class="section-header">Note</div>
    <div class="notes-body"></div>
  </div>
</div>"""


# ─── Hierarchy traversal ──────────────────────────────────────────────────────

def _collect_cards(project, db: Session) -> list[str]:
    cards: list[str] = []
    proj_code = project.code or ""
    proj_name = project.name or ""
    project_id = project.id

    for item in (project.items or []):
        product_id = item.get("productId")
        if not product_id:
            continue
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            continue

        # Resolve assemblies for this product up front — reused for both the
        # product card's composition summary and the assembly cards below.
        if product.product_assemblies:
            asm_ids = [a["assemblyId"] for a in product.product_assemblies if a.get("assemblyId")]
        else:
            asm_ids = product.assembly_ids or []
        assemblies_by_id = {
            a.id: a for a in (db.query(Assembly).filter(Assembly.id.in_(asm_ids)).all() if asm_ids else [])
        }
        ordered_assemblies = [assemblies_by_id[aid] for aid in asm_ids if aid in assemblies_by_id]

        # Resolve direct parts for this product up front — same reuse as above.
        if product.product_parts:
            direct_ids = [p["partId"] for p in product.product_parts if p.get("partId")]
        else:
            direct_ids = product.part_ids or []
        direct_parts_by_id = {
            p.id: p for p in (db.query(Part).filter(Part.id.in_(direct_ids)).all() if direct_ids else [])
        }
        ordered_direct_parts = [direct_parts_by_id[pid] for pid in direct_ids if pid in direct_parts_by_id]

        composition = (
            [{"type_label": "Ansamblu", "name": a.name, "entity_type": "assembly", "entity_id": a.id, "code": a.code}
             for a in ordered_assemblies]
            + [{"type_label": "Piesă directă", "name": p.name, "entity_type": "part", "entity_id": p.id, "code": p.code or ""}
               for p in ordered_direct_parts]
        )

        # Product card — summarizes what it's made of so it's never empty
        prod_steps = product.production_steps or product.assembly_steps or []
        cards.append(_card("product", product.id, product.name, product.code,
                           "Produs", prod_steps, proj_code, proj_name, db,
                           project_id=project_id, composition=composition))

        # Assembly cards + their part cards (fully recursive via iter_assembly_nodes)
        for asm_id in asm_ids:
            for asm, depth in iter_assembly_nodes(asm_id, db):
                type_label = "Ansamblu" if depth == 0 else f"Sub-ansamblu (niv. {depth})"
                cards.append(_card("assembly", asm.id, asm.name, asm.code,
                                   type_label, asm.production_steps or [], proj_code, proj_name, db,
                                   project_id=project_id))

                for ap in (asm.parts or []):
                    pid = ap.get("partId")
                    if not pid:
                        continue
                    part = db.query(Part).filter(Part.id == pid).first()
                    if not part:
                        continue
                    cards.append(_card("part", part.id, part.name, part.code or "",
                                       "Piesă", part.production_steps or [], proj_code, proj_name, db,
                                       project_id=project_id))

        # Direct part cards
        for part in ordered_direct_parts:
            cards.append(_card("part", part.id, part.name, part.code or "",
                               "Piesă directă", part.production_steps or [], proj_code, proj_name, db,
                               project_id=project_id))

    return cards


# ─── Public entry point ───────────────────────────────────────────────────────

def generate_production_cards_pdf(project, db: Session) -> bytes:
    from weasyprint import HTML

    cards = _collect_cards(project, db)

    if not cards:
        return HTML(string=(
            '<!DOCTYPE html><html><body style="font-family:Arial;padding:24px;">'
            '<h2>Fișe de producție</h2>'
            f'<p style="color:#888;margin-top:12px;">Niciun produs / ansamblu / piesă în proiectul &quot;{project.name}&quot;.</p>'
            '</body></html>'
        )).write_pdf()

    pairs = []
    for i in range(0, len(cards), 2):
        c1 = cards[i]
        c2 = cards[i + 1] if i + 1 < len(cards) else ""
        pairs.append(f'<div class="card-pair">{c1}{c2}</div>')

    return HTML(string=_HTML_WRAPPER.format(css=_CSS, pairs="".join(pairs))).write_pdf()
