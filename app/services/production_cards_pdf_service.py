"""
Production cards PDF service.

Grouping rules:
  - Products: one card per project item (not grouped).
  - Assemblies and Parts: grouped by (entity_type, entity_id) across all products
    and assemblies in the project.  Each group shows total combined quantity and
    lists every parent where the item is used.

Layout:
  4 cards per A4 portrait page in a 2×2 grid — fills left-to-right (FILL PE RAND).
"""

import os
import base64
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.assembly import Assembly
from app.models.part import Part
from app.models.uploaded_file import UploadedFile
from app.services.assembly_tree import iter_assembly_nodes
from app.services.dxf_utils import render_dxf_to_data_uri

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
        preview = render_dxf_to_data_uri(first_dxf_path)
        if preview:
            return preview

    return _make_file_badge(fallback_label) if fallback_label else _PLACEHOLDER_URI


# ─── CSS ──────────────────────────────────────────────────────────────────────

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: A4 portrait; margin: 6mm; }
body { font-family: Arial, sans-serif; font-size: 9pt; color: #000; background: #fff; }

/* ── Page: 2 wide horizontal cards stacked per A4 page ── */
.page {
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
  width: 198mm;
  height: 285mm;
  page-break-after: always;
  break-after: page;
}
.page:last-child { page-break-after: avoid; break-after: avoid; }

/* ── Card shell ── */
.card {
  border: 2px solid #000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex: 0 1 132mm;   /* wide + roughly half-page tall */
}
.card-empty {
  border: 1px dashed #ccc;
  background: #fafafa;
  flex: 0 1 132mm;
}

/* ── Header row: icon | info ── */
.card-top {
  display: flex;
  flex-direction: row;
  border-bottom: 2px solid #000;
  flex-shrink: 0;
  min-height: 32mm;
  max-height: 42mm;
}

.card-icon {
  width: 32mm;
  flex-shrink: 0;
  border-right: 1.5px solid #999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  background: #fff;
}
.card-icon img {
  max-width: 28mm;
  max-height: 30mm;
  object-fit: contain;
}

.card-info {
  flex: 1;
  position: relative;
  padding-bottom: 16mm;
  overflow: hidden;
}
.info-type {
  font-size: 5.5pt;
  color: #777;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 3px 6px 0;
}
.info-name {
  font-size: 11pt;
  font-weight: bold;
  line-height: 1.1;
  padding: 1px 6px 3px;
  border-bottom: 1px solid #ccc;
  word-break: break-word;
}
.info-qty {
  font-size: 8pt;
  font-weight: bold;
  padding: 2px 6px;
  color: #333;
  border-bottom: 1px solid #eee;
}
.info-project {
  font-size: 7pt;
  padding: 2px 6px;
  border-bottom: 1px solid #ccc;
  color: #333;
}
.info-project strong { font-weight: 700; color: #000; }
.info-barcode {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 2px 6px 3px;
}
.barcode-lbl {
  font-size: 5.5pt;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: #888;
  margin-bottom: 1px;
}
.barcode-bars {
  width: 44mm;
  height: 9mm;
  margin-bottom: 1px;
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
  font-size: 6pt;
  color: #222;
  letter-spacing: 0.4px;
}

/* ── Steps ── */
.card-steps {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-bottom: 1.5px solid #000;
  min-height: 0;
  overflow: hidden;
}
.section-header {
  font-size: 5.5pt;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #fff;
  background: #000;
  padding: 2px 8px;
  flex-shrink: 0;
}
.step-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 2px 8px;
  border-bottom: 1px solid #eee;
  min-height: 6mm;
}
.step-row:last-child { border-bottom: none; }
.step-cb {
  width: 9px; height: 9px;
  border: 1.5px solid #000;
  flex-shrink: 0;
  display: inline-block;
}
.step-num {
  font-size: 6.5pt; color: #999;
  flex-shrink: 0; min-width: 14px;
  font-family: monospace;
}
.step-name { font-size: 8pt; font-weight: 600; flex: 1; }
.step-type {
  font-size: 5.5pt; color: #666;
  background: #f0f0f0;
  border-radius: 2px;
  padding: 1px 3px;
  flex-shrink: 0;
}
.no-steps {
  padding: 4px 8px;
  font-size: 7pt;
  color: #bbb;
  font-style: italic;
}

/* ── Composition / Usage ── */
.comp-header, .usage-header {
  font-size: 5.5pt;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: #555;
  background: #f0f0f0;
  padding: 2px 8px;
  border-top: 1px solid #ccc;
  flex-shrink: 0;
}
.comp-row, .usage-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  padding: 2px 8px;
  border-bottom: 1px solid #eee;
  min-height: 5.5mm;
}
.comp-row:last-child, .usage-row:last-child { border-bottom: none; }
.comp-type-lbl { font-size: 6pt; color: #666; font-weight: 600; flex-shrink: 0; min-width: 20mm; }
.comp-name, .usage-name { font-size: 8pt; font-weight: 600; flex: 1; overflow: hidden; }
.comp-qty, .usage-qty { font-size: 7pt; color: #333; flex-shrink: 0; font-weight: bold; }
.usage-total {
  font-weight: bold;
  border-top: 1.5px solid #bbb;
  background: #f8f8f8;
}

/* ── Notes ── */
.card-notes {
  flex-shrink: 0;
  min-height: 10mm;
  max-height: 14mm;
}
.notes-body {
  min-height: 7mm;
}
"""

_HTML_WRAPPER = """<!DOCTYPE html>
<html lang="ro">
<head><meta charset="UTF-8"/><style>{css}</style></head>
<body>{pages}</body>
</html>"""


# ─── Barcode payload helpers ──────────────────────────────────────────────────

def build_project_item_barcode_payload(project_id: str, entity_type: str, entity_id: str, code: str) -> str:
    return (
        f"PROJECT_ITEM|projectId={project_id}|entityType={entity_type}"
        f"|entityId={entity_id}|code={code or ''}"
    )


def build_project_step_barcode_payload(project_id: str, entity_type: str, entity_id: str, step_id: str) -> str:
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
        display = name + (f' <span style="font-size:7pt;color:#777;font-weight:normal;">— {desc}</span>' if desc else "")
        type_badge = f'<span class="step-type">{stype}</span>' if stype else ""
        step_payload_attr = ""
        if step_id:
            payload = build_project_step_barcode_payload(project_id, entity_type, entity_id, step_id)
            step_payload_attr = f' data-step-payload="{payload}"'
        html += (
            f'<div class="step-row"{step_payload_attr}>'
            f'<span class="step-cb"></span>'
            f'<span class="step-num">{i + 1}.</span>'
            f'<span class="step-name">{display}</span>'
            f'{type_badge}'
            f'</div>'
        )
    return html


def _composition_rows(items: list[dict], project_id: str) -> str:
    """Product composition: lists assemblies and direct parts with their quantities."""
    if not items:
        return ""
    rows = ""
    for it in items:
        payload = build_project_item_barcode_payload(
            project_id, it["entity_type"], it["entity_id"], it.get("code", "")
        )
        qty_label = f'×{it["quantity"]}' if it.get("quantity") and it["quantity"] != 1 else ""
        rows += (
            f'<div class="comp-row" data-item-payload="{payload}">'
            f'<span class="comp-type-lbl">{it["type_label"]}</span>'
            f'<span class="comp-name">{it["name"]}</span>'
            f'<span class="comp-qty">{qty_label}</span>'
            f'</div>'
        )
    return f'<div class="comp-header">Compoziție produs</div>{rows}'


def _usage_rows(usages: list[dict], total_qty: float) -> str:
    """Usage section for grouped assembly/part cards: shows all parents and total qty."""
    if not usages:
        return ""
    rows = ""
    for u in usages:
        parent_label = u["parent_name"]
        if u.get("parent_code"):
            parent_label += f' ({u["parent_code"]})'
        qty_label = f'×{_fmt_qty(u["quantity"])}'
        rows += (
            f'<div class="usage-row">'
            f'<span class="usage-name">{parent_label}</span>'
            f'<span class="usage-qty">{qty_label}</span>'
            f'</div>'
        )
    total_label = f'×{_fmt_qty(total_qty)}'
    rows += (
        f'<div class="usage-row usage-total">'
        f'<span class="usage-name">Total</span>'
        f'<span class="usage-qty">{total_label}</span>'
        f'</div>'
    )
    return f'<div class="usage-header">Utilizat în</div>{rows}'


def _fmt_qty(q: float) -> str:
    """Format quantity: drop .0 if it's a whole number."""
    return str(int(q)) if q == int(q) else f"{q:.2f}".rstrip("0").rstrip(".")


def _card(
    entity_type: str,
    entity_id: str,
    name: str,
    code: str,
    type_label: str,
    steps: list,
    proj_code: str,
    proj_name: str,
    db: Session,
    project_id: str,
    composition: list[dict] | None = None,
    total_qty: float | None = None,
    usages: list[dict] | None = None,
) -> str:
    img = _icon(entity_type, entity_id, db)
    barcode_display = code or entity_id[:12].upper()
    payload = build_project_item_barcode_payload(project_id, entity_type, entity_id, code)

    # Quantity header line (shown when total_qty provided, i.e. for grouped cards)
    qty_html = ""
    if total_qty is not None:
        qty_html = f'<div class="info-qty">Total: ×{_fmt_qty(total_qty)}</div>'

    # Steps section
    steps_html = _steps_rows(steps, project_id, entity_type, entity_id)
    steps_content = steps_html or '<div class="no-steps">— Nicio etapă de producție —</div>'

    # Composition (for products) or usage (for grouped assemblies/parts)
    extra_html = ""
    if composition:
        extra_html = _composition_rows(composition, project_id)
    elif usages:
        extra_html = _usage_rows(usages, total_qty or 0)

    return f"""
<div class="card">
  <div class="card-top">
    <div class="card-icon"><img src="{img}" alt=""/></div>
    <div class="card-info">
      <div class="info-type">{type_label}</div>
      <div class="info-name">{name}</div>
      {qty_html}
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
    {steps_content}
  </div>
  {extra_html}
  <div class="card-notes">
    <div class="section-header">Note</div>
    <div class="notes-body"></div>
  </div>
</div>"""


# ─── Grouping helpers ─────────────────────────────────────────────────────────

def _add_to_group(
    groups: dict,
    entity_id: str,
    entity_obj,
    quantity: float,
    parent_name: str,
    parent_code: str,
) -> None:
    """Add an entity occurrence to its group, accumulating quantity and usage info."""
    if entity_id not in groups:
        groups[entity_id] = {
            "obj": entity_obj,
            "total_qty": 0.0,
            "usages": [],
        }
    groups[entity_id]["total_qty"] += quantity
    groups[entity_id]["usages"].append({
        "parent_name": parent_name,
        "parent_code": parent_code,
        "quantity": quantity,
    })


def _collect_asm_tree(
    asm_id: str,
    item_qty: float,
    parent_name: str,
    parent_code: str,
    db: Session,
    asm_groups: dict,
    part_groups: dict,
    _visited: frozenset | None = None,
) -> None:
    """Recursively collect assembly and all descendants, registering each into groups."""
    _visited = _visited or frozenset()
    if asm_id in _visited:
        return
    _visited = _visited | {asm_id}

    asm = db.query(Assembly).filter(Assembly.id == asm_id).first()
    if not asm:
        return

    # Register this assembly
    _add_to_group(asm_groups, asm.id, asm, item_qty, parent_name, parent_code)

    # Register parts of this assembly
    for ap in (asm.parts or []):
        pid = ap.get("partId")
        if not pid:
            continue
        part_qty = (ap.get("quantity") or 1) * item_qty
        part = db.query(Part).filter(Part.id == pid).first()
        if part:
            _add_to_group(part_groups, pid, part, part_qty, asm.name, asm.code or "")

    # Recurse into child assemblies with their own multipliers
    for ca in (asm.child_assemblies or []):
        child_id = ca.get("assemblyId")
        if not child_id:
            continue
        child_qty = (ca.get("quantity") or 1) * item_qty
        _collect_asm_tree(
            child_id, child_qty, asm.name, asm.code or "",
            db, asm_groups, part_groups, _visited,
        )


# ─── Main collection ─────────────────────────────────────────────────────────

def _collect_cards(project, db: Session) -> list[str]:
    from app.routers.projects import _item_kind

    proj_code = project.code or ""
    proj_name = project.name or ""
    project_id = project.id

    # Groups: keyed by entity_id, accumulate qty and usage list
    asm_groups: dict[str, dict] = {}
    part_groups: dict[str, dict] = {}

    product_cards_html: list[str] = []

    for item in (project.items or []):
        kind, eid = _item_kind(item)
        item_qty = float(item.get("quantity") or 1)

        if kind == "product":
            product = db.query(Product).filter(Product.id == eid).first()
            if not product:
                continue

            # ── Assembly entries for this product ──
            if product.product_assemblies:
                asm_entries = product.product_assemblies
            else:
                asm_entries = [{"assemblyId": aid, "quantity": 1} for aid in (product.assembly_ids or [])]

            # ── Direct part entries for this product ──
            if product.product_parts:
                part_entries = product.product_parts
            else:
                part_entries = [{"partId": pid, "quantity": 1} for pid in (product.part_ids or [])]

            # Build composition data for the product card
            asm_ids = [e.get("assemblyId") for e in asm_entries if e.get("assemblyId")]
            assemblies_by_id = {
                a.id: a
                for a in (db.query(Assembly).filter(Assembly.id.in_(asm_ids)).all() if asm_ids else [])
            }
            ordered_assemblies = [assemblies_by_id[aid] for aid in asm_ids if aid in assemblies_by_id]

            direct_ids = [e.get("partId") for e in part_entries if e.get("partId")]
            direct_parts_by_id = {
                p.id: p
                for p in (db.query(Part).filter(Part.id.in_(direct_ids)).all() if direct_ids else [])
            }
            ordered_direct_parts = [direct_parts_by_id[pid] for pid in direct_ids if pid in direct_parts_by_id]

            # Quantity helpers
            asm_qty_map = {e.get("assemblyId"): (e.get("quantity") or 1) for e in asm_entries}
            part_qty_map = {e.get("partId"): (e.get("quantity") or 1) for e in part_entries}

            composition = (
                [
                    {
                        "type_label": "Ansamblu",
                        "name": a.name,
                        "entity_type": "assembly",
                        "entity_id": a.id,
                        "code": a.code,
                        "quantity": asm_qty_map.get(a.id, 1),
                    }
                    for a in ordered_assemblies
                ]
                + [
                    {
                        "type_label": "Piesă directă",
                        "name": p.name,
                        "entity_type": "part",
                        "entity_id": p.id,
                        "code": p.code or "",
                        "quantity": part_qty_map.get(p.id, 1),
                    }
                    for p in ordered_direct_parts
                ]
            )

            prod_steps = product.production_steps or product.assembly_steps or []
            product_cards_html.append(
                _card(
                    "product", product.id, product.name, product.code,
                    "Produs", prod_steps, proj_code, proj_name, db,
                    project_id=project_id, composition=composition,
                )
            )

            # Register assemblies (and their trees) for grouping
            for a in ordered_assemblies:
                qty = asm_qty_map.get(a.id, 1) * item_qty
                _collect_asm_tree(
                    a.id, qty, product.name, product.code or "",
                    db, asm_groups, part_groups,
                )

            # Register direct parts of the product for grouping
            for p in ordered_direct_parts:
                qty = part_qty_map.get(p.id, 1) * item_qty
                _add_to_group(part_groups, p.id, p, qty, product.name, product.code or "")

        elif kind == "assembly":
            asm = db.query(Assembly).filter(Assembly.id == eid).first()
            if not asm:
                continue
            _collect_asm_tree(
                eid, item_qty, "Proiect direct", proj_code,
                db, asm_groups, part_groups,
            )

        elif kind == "part":
            part = db.query(Part).filter(Part.id == eid).first()
            if not part:
                continue
            _add_to_group(part_groups, eid, part, item_qty, "Proiect direct", proj_code)

    # ── Generate cards in order: products → assemblies → parts ──
    cards: list[str] = list(product_cards_html)

    for asm_id, spec in asm_groups.items():
        asm = spec["obj"]
        total_qty = spec["total_qty"]
        usages = spec["usages"]
        cards.append(
            _card(
                "assembly", asm.id, asm.name, asm.code or "",
                "Ansamblu", asm.production_steps or [],
                proj_code, proj_name, db,
                project_id=project_id,
                total_qty=total_qty,
                usages=usages,
            )
        )

    for part_id, spec in part_groups.items():
        part = spec["obj"]
        total_qty = spec["total_qty"]
        usages = spec["usages"]
        cards.append(
            _card(
                "part", part.id, part.name, part.code or "",
                "Piesă", part.production_steps or [],
                proj_code, proj_name, db,
                project_id=project_id,
                total_qty=total_qty,
                usages=usages,
            )
        )

    return cards


# ─── Public entry point ───────────────────────────────────────────────────────

def generate_production_cards_pdf(project, db: Session) -> bytes:
    from weasyprint import HTML

    cards = _collect_cards(project, db)

    if not cards:
        return HTML(string=(
            '<!DOCTYPE html><html><body style="font-family:Arial;padding:24px;">'
            '<h2>Fișe de producție</h2>'
            f'<p style="color:#888;margin-top:12px;">Niciun produs / ansamblu / piesă '
            f'în proiectul &quot;{project.name}&quot;.</p>'
            '</body></html>'
        )).write_pdf()

    # 2 cards per page, side-by-side (left-to-right)
    pages = []
    for i in range(0, len(cards), 2):
        group = cards[i:i + 2]
        # Pad last page with empty placeholder div to maintain grid shape
        while len(group) < 2:
            group.append('<div class="card card-empty"></div>')
        pages.append(f'<div class="page">{"".join(group)}</div>')

    return HTML(
        string=_HTML_WRAPPER.format(css=_CSS, pages="".join(pages))
    ).write_pdf()
