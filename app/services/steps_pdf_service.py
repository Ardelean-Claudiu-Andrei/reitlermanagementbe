from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.assembly import Assembly
from app.models.part import Part
from app.services.assembly_tree import iter_assembly_nodes

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ro">
<head>
  <meta charset="UTF-8"/>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    @page {{ size: A4; margin: 18mm 15mm; }}
    body {{ font-family: Arial, sans-serif; font-size: 10pt; color: #111; }}

    /* Page header */
    .doc-header {{ border-bottom: 2px solid #1a1a2e; padding-bottom: 8px; margin-bottom: 16px; }}
    .doc-title {{ font-size: 16pt; font-weight: bold; color: #1a1a2e; }}
    .doc-subtitle {{ font-size: 9pt; color: #666; margin-top: 2px; }}
    .footer {{ margin-top: 20px; font-size: 8pt; color: #999; border-top: 1px solid #ddd; padding-top: 6px; }}

    /* Product section */
    .product-block {{ margin-bottom: 24px; }}
    .product-title {{
      font-size: 12pt;
      font-weight: bold;
      color: #1a1a2e;
      border-bottom: 1.5px solid #1a1a2e;
      padding-bottom: 4px;
      margin-bottom: 10px;
    }}
    .product-code {{ font-family: monospace; font-size: 9pt; color: #666; font-weight: normal; margin-left: 8px; }}

    /* Assembly section */
    .assembly-section {{ margin: 8px 0 8px 12px; }}
    .assembly-title {{
      font-size: 10pt;
      font-weight: bold;
      color: #2a3a5e;
      border-left: 3px solid #c0c8e0;
      padding-left: 8px;
      margin-bottom: 4px;
    }}
    .assembly-code-label {{ font-family: monospace; font-size: 8pt; color: #888; font-weight: normal; }}

    /* Part section */
    .part-section {{ margin: 6px 0 6px 20px; }}
    .part-title {{
      font-size: 9pt;
      font-weight: 600;
      color: #444;
      border-left: 2px solid #e0e0e0;
      padding-left: 6px;
      margin-bottom: 3px;
    }}
    .part-direct-label {{ font-size: 8pt; color: #888; font-style: italic; }}
    .laser-label {{ font-size: 8pt; color: #1a6fa8; }}

    /* Step rows */
    .steps-list {{ margin: 2px 0 6px 0; }}
    .step-row {{ display: flex; align-items: flex-start; gap: 8px; padding: 3px 0; }}
    .step-checkbox {{
      width: 13px; height: 13px;
      border: 1.5px solid #444;
      flex-shrink: 0; margin-top: 1px;
      display: inline-block;
    }}
    .step-num {{ font-size: 9pt; color: #888; flex-shrink: 0; min-width: 18px; }}
    .step-content {{ flex: 1; }}
    .step-name {{ font-size: 10pt; }}
    .step-desc {{ font-size: 8.5pt; color: #666; margin-top: 1px; padding-left: 26px; }}

    .separator {{ border: none; border-top: 1px solid #e8e8e8; margin: 14px 0; }}
    .no-steps {{ color: #aaa; font-size: 9pt; font-style: italic; }}
  </style>
</head>
<body>
  <div class="doc-header">
    <div class="doc-title">Etapele Producției</div>
    <div class="doc-subtitle">{subtitle}</div>
  </div>
  {content}
  <div class="footer">Generat automat &mdash; SMS Reitler</div>
</body>
</html>
"""


def _render_step(step: dict, index: int) -> str:
    name = step.get("name", "")
    desc = step.get("description", "")
    desc_html = f'<div class="step-desc">{desc}</div>' if desc else ""
    return f"""
    <div class="step-row">
      <span class="step-checkbox"></span>
      <span class="step-num">{index}.</span>
      <div class="step-content">
        <span class="step-name">{name}</span>
        {desc_html}
      </div>
    </div>"""


def _render_steps(steps: list) -> str:
    if not steps:
        return '<div class="no-steps">—</div>'
    return f'<div class="steps-list">{"".join(_render_step(s, i + 1) for i, s in enumerate(steps))}</div>'


def _render_assembly(asm: Assembly, db: Session, depth: int = 0) -> str:
    """Render one assembly section with its parts and child assemblies, recursively."""
    asm_steps: list = asm.production_steps or []
    asm_inner = []
    if asm_steps:
        asm_inner.append(_render_steps(asm_steps))

    for ap in (asm.parts or []):
        part_id = ap.get("partId")
        if not part_id:
            continue
        part = db.query(Part).filter(Part.id == part_id).first()
        if not part:
            continue
        part_steps: list = part.production_steps or []
        if not part_steps:
            continue
        laser_label = ' <span class="laser-label">⚡ Laser</span>' if part.requires_laser_cutting else ""
        asm_inner.append(f"""
            <div class="part-section">
              <div class="part-title">Piesă: {part.name}{laser_label}</div>
              {_render_steps(part_steps)}
            </div>""")

    for ca in (asm.child_assemblies or []):
        child_id = ca.get("assemblyId")
        if not child_id:
            continue
        child_asm = db.query(Assembly).filter(Assembly.id == child_id).first()
        if not child_asm:
            continue
        child_html = _render_assembly(child_asm, db, depth + 1)
        if child_html:
            asm_inner.append(child_html)

    if not asm_inner:
        return ""

    indent = 12 + depth * 12
    return f"""
        <div class="assembly-section" style="margin-left:{indent}px">
          <div class="assembly-title">Ansamblu: {asm.name} <span class="assembly-code-label">{asm.code}</span></div>
          {"".join(asm_inner)}
        </div>"""


def _build_product_html(product: Product, db: Session) -> str:
    product_steps: list = product.production_steps or product.assembly_steps or []

    body_parts = []

    # Product-level steps
    if product_steps:
        body_parts.append(_render_steps(product_steps))

    # Assembly nodes (recursive)
    if product.product_assemblies:
        asm_ids = [a["assemblyId"] for a in product.product_assemblies if a.get("assemblyId")]
    else:
        asm_ids = product.assembly_ids or []

    for asm_id in asm_ids:
        asm = db.query(Assembly).filter(Assembly.id == asm_id).first()
        if not asm:
            continue
        html = _render_assembly(asm, db)
        if html:
            body_parts.append(html)

    # Direct parts
    if product.product_parts:
        direct_ids = [p["partId"] for p in product.product_parts if p.get("partId")]
    else:
        direct_ids = product.part_ids or []

    for part_id in direct_ids:
        part = db.query(Part).filter(Part.id == part_id).first()
        if not part:
            continue
        part_steps: list = part.production_steps or []
        if not part_steps:
            continue
        laser_label = ' <span class="laser-label">⚡ Laser</span>' if part.requires_laser_cutting else ""
        body_parts.append(f"""
        <div class="part-section">
          <div class="part-title">Piesă directă: {part.name}{laser_label} <span class="part-direct-label">(direct)</span></div>
          {_render_steps(part_steps)}
        </div>""")

    if not body_parts:
        body = '<div class="no-steps">Nu există pași de producție pentru acest produs.</div>'
    else:
        body = "".join(body_parts)

    return f"""
    <div class="product-block">
      <div class="product-title">Produs: {product.name} <span class="product-code">{product.code}</span></div>
      {body}
    </div>
    <hr class="separator"/>"""


def generate_product_steps_pdf(product: Product, db: Session) -> bytes:
    from weasyprint import HTML

    subtitle = f"Produs: {product.name} — Cod: {product.code}"
    content = _build_product_html(product, db)
    html = HTML_TEMPLATE.format(subtitle=subtitle, content=content)
    return HTML(string=html).write_pdf()


def generate_project_steps_pdf(project, db: Session) -> bytes:
    """Generate a steps PDF for all products in a project."""
    from weasyprint import HTML

    subtitle = f"Proiect: {project.name} — Cod: {project.code}"
    content_parts = []
    for item in (project.items or []):
        product_id = item.get("productId")
        if not product_id:
            continue
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            continue
        content_parts.append(_build_product_html(product, db))

    content = "".join(content_parts) if content_parts else '<p class="no-steps">Nu există pași de producție.</p>'
    html = HTML_TEMPLATE.format(subtitle=subtitle, content=content)
    return HTML(string=html).write_pdf()
