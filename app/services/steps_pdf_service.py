from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.assembly import Assembly
from app.models.part import Part

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ro">
<head>
  <meta charset="UTF-8"/>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: Arial, sans-serif; font-size: 10pt; color: #111; padding: 24px; }}
    h1 {{ font-size: 15pt; margin-bottom: 2px; }}
    .subtitle {{ font-size: 9pt; color: #666; margin-bottom: 20px; }}
    .footer {{ margin-top: 24px; font-size: 8pt; color: #999; border-top: 1px solid #ddd; padding-top: 8px; }}

    /* Product block */
    .product-block {{ margin-bottom: 28px; page-break-inside: avoid; }}
    .product-header {{
      background: #1a1a2e;
      color: #fff;
      padding: 8px 12px;
      border-radius: 4px 4px 0 0;
      font-size: 11pt;
      font-weight: bold;
      display: flex;
      justify-content: space-between;
    }}
    .product-header .code {{ font-family: monospace; font-size: 9pt; opacity: 0.8; }}
    .product-body {{ border: 1px solid #ccc; border-top: none; border-radius: 0 0 4px 4px; padding: 8px 12px; }}

    /* Step rows */
    .step-row {{ display: flex; align-items: flex-start; gap: 8px; padding: 5px 0; border-bottom: 1px solid #f0f0f0; }}
    .step-row:last-child {{ border-bottom: none; }}
    .step-checkbox {{ width: 14px; height: 14px; border: 1.5px solid #555; flex-shrink: 0; margin-top: 2px; }}
    .step-content {{ flex: 1; }}
    .step-name {{ font-weight: bold; font-size: 10pt; }}
    .step-type {{ display: inline-block; background: #e8f4fd; color: #1a6fa8; border: 1px solid #b3d7f5; border-radius: 3px; padding: 0 5px; font-size: 8pt; font-family: monospace; margin-left: 6px; }}
    .step-desc {{ font-size: 9pt; color: #666; margin-top: 2px; }}

    /* Assembly block */
    .assembly-block {{ margin: 8px 0 8px 16px; border: 1px solid #ddd; border-radius: 3px; }}
    .assembly-header {{ background: #f0f4f8; padding: 5px 10px; font-weight: bold; font-size: 9pt; border-bottom: 1px solid #ddd; display: flex; gap: 8px; align-items: center; }}
    .assembly-code {{ font-family: monospace; font-size: 8pt; color: #888; }}
    .assembly-body {{ padding: 4px 10px; }}

    /* Part block */
    .part-block {{ margin: 6px 0 6px 16px; border: 1px solid #e8e8e8; border-radius: 3px; }}
    .part-header {{ background: #fafafa; padding: 4px 8px; font-weight: 600; font-size: 9pt; border-bottom: 1px solid #e8e8e8; display: flex; gap: 6px; align-items: center; }}
    .part-direct {{ color: #888; font-size: 8pt; font-style: italic; }}
    .laser-tag {{ color: #1a6fa8; font-size: 8pt; }}
    .part-body {{ padding: 4px 8px; }}

    .no-steps {{ color: #aaa; font-size: 9pt; font-style: italic; padding: 4px 0; }}
  </style>
</head>
<body>
  <h1>Etapele Producției</h1>
  <p class="subtitle">{subtitle}</p>
  {content}
  <div class="footer">Generat automat &mdash; SMS Reitler</div>
</body>
</html>
"""


def _render_step(step: dict, index: int) -> str:
    name = step.get("name", "")
    step_type = step.get("type", "")
    desc = step.get("description", "")
    type_tag = f'<span class="step-type">{step_type}</span>' if step_type else ""
    desc_html = f'<div class="step-desc">{desc}</div>' if desc else ""
    return f"""
    <div class="step-row">
      <div class="step-checkbox"></div>
      <div class="step-content">
        <span class="step-name">{index}. {name}</span>{type_tag}
        {desc_html}
      </div>
    </div>"""


def _render_steps(steps: list) -> str:
    if not steps:
        return '<div class="no-steps">—</div>'
    return "".join(_render_step(s, i + 1) for i, s in enumerate(steps))


def _build_product_html(product: Product, db: Session) -> str:
    product_steps: list = product.production_steps or product.assembly_steps or []

    # Collect assembly nodes
    assembly_htmls = []
    for asm_id in (product.assembly_ids or []):
        asm = db.query(Assembly).filter(Assembly.id == asm_id).first()
        if not asm:
            continue
        asm_steps: list = asm.production_steps or []
        asm_steps_html = _render_steps(asm_steps)

        # Parts within assembly
        part_htmls = []
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
            laser_tag = '<span class="laser-tag">⚡ Laser</span>' if part.requires_laser_cutting else ""
            part_htmls.append(f"""
            <div class="part-block">
              <div class="part-header">Piesă: {part.name}{laser_tag}</div>
              <div class="part-body">{_render_steps(part_steps)}</div>
            </div>""")

        parts_html = "".join(part_htmls)
        if not asm_steps and not parts_html:
            continue

        assembly_htmls.append(f"""
        <div class="assembly-block">
          <div class="assembly-header">
            Ansamblu: {asm.name}
            <span class="assembly-code">{asm.code}</span>
          </div>
          <div class="assembly-body">
            {asm_steps_html if asm_steps else ""}
            {parts_html}
          </div>
        </div>""")

    # Direct parts
    direct_part_htmls = []
    for part_id in (product.part_ids or []):
        part = db.query(Part).filter(Part.id == part_id).first()
        if not part:
            continue
        part_steps: list = part.production_steps or []
        if not part_steps:
            continue
        laser_tag = '<span class="laser-tag">⚡ Laser</span>' if part.requires_laser_cutting else ""
        direct_part_htmls.append(f"""
        <div class="part-block">
          <div class="part-header">
            Piesă directă: {part.name}{laser_tag}
            <span class="part-direct"></span>
          </div>
          <div class="part-body">{_render_steps(part_steps)}</div>
        </div>""")

    assemblies_html = "".join(assembly_htmls)
    direct_parts_html = "".join(direct_part_htmls)
    product_steps_html = _render_steps(product_steps) if product_steps else ""

    body = product_steps_html + assemblies_html + direct_parts_html
    if not body.strip():
        body = '<div class="no-steps">Nu există pași de producție pentru acest produs.</div>'

    return f"""
    <div class="product-block">
      <div class="product-header">
        <span>Produs: {product.name}</span>
        <span class="code">{product.code}</span>
      </div>
      <div class="product-body">{body}</div>
    </div>"""


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
