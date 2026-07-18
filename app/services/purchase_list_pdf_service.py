from datetime import datetime
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.part import Part
from app.services.assembly_tree import iter_assembly_parts

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ro">
<head>
  <meta charset="UTF-8"/>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    @page {{ size: A4; margin: 18mm 15mm; }}
    body {{ font-family: Arial, sans-serif; font-size: 10pt; color: #111; }}

    .doc-header {{
      border-bottom: 2px solid #ea580c;
      padding-bottom: 8px;
      margin-bottom: 16px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }}
    .doc-title {{ font-size: 16pt; font-weight: bold; color: #1a1a2e; }}
    .doc-subtitle {{ font-size: 9pt; color: #666; margin-top: 3px; }}
    .doc-meta {{ font-size: 8pt; color: #888; text-align: right; }}

    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
      font-size: 9pt;
    }}
    thead th {{
      background: #1a1a2e;
      color: #fff;
      padding: 6px 8px;
      text-align: left;
      font-weight: bold;
      font-size: 8pt;
      letter-spacing: 0.03em;
    }}
    thead th.right {{ text-align: right; }}
    tbody tr:nth-child(even) {{ background: #f8f9fb; }}
    tbody tr {{ border-bottom: 1px solid #e8eaed; }}
    tbody td {{ padding: 6px 8px; vertical-align: top; }}
    tbody td.right {{ text-align: right; }}

    .name {{ font-weight: bold; color: #1a1a2e; }}
    .code {{ font-family: monospace; font-size: 7.5pt; color: #777; display: block; margin-top: 1px; }}

    .vat-badge {{
      display: inline-block;
      background: #fef3c7;
      color: #92400e;
      border-radius: 3px;
      padding: 1px 4px;
      font-size: 7.5pt;
      font-weight: bold;
      margin-left: 4px;
    }}

    .footer {{
      margin-top: 20px;
      font-size: 7.5pt;
      color: #aaa;
      border-top: 1px solid #e0e0e0;
      padding-top: 6px;
      display: flex;
      justify-content: space-between;
    }}

    .summary-box {{
      margin-top: 16px;
      padding: 10px 12px;
      background: #fff7ed;
      border: 1px solid #fed7aa;
      border-radius: 6px;
      font-size: 9pt;
      color: #7c2d12;
    }}
    .summary-box strong {{ font-size: 10pt; }}
  </style>
</head>
<body>
  <div class="doc-header">
    <div>
      <div class="doc-title">Piese de achiziționat</div>
      <div class="doc-subtitle">Proiect: {project_name} &nbsp;·&nbsp; Cod: {project_code}</div>
    </div>
    <div class="doc-meta">Generat: {generated_at}</div>
  </div>

  {table_html}

  <div class="summary-box">
    <strong>{part_count} {part_label}</strong> necesită achiziție externă · {total_qty} bucăți în total
  </div>

  <div class="footer">
    <span>SMS Reitler &mdash; Listă achiziții proiect {project_code}</span>
    <span>{generated_at}</span>
  </div>
</body>
</html>
"""

ROW_TEMPLATE = """
<tr>
  <td>
    <span class="name">{name}</span>
    {code_html}
  </td>
  <td class="right">{quantity}</td>
  <td>{supplier}</td>
  <td>
    {price_html}
  </td>
  <td>{contact}</td>
</tr>
"""


def _price_html(part: Part) -> str:
    if part.purchase_price is None:
        return "—"
    currency = part.purchase_currency or "EUR"
    price_str = f"{part.purchase_price:g} {currency}"
    if part.purchase_vat_included:
        rate = int(part.purchase_vat_rate) if part.purchase_vat_rate == int(part.purchase_vat_rate) else part.purchase_vat_rate
        return f'{price_str} <span class="vat-badge">TVA {rate}%</span>'
    return f"{price_str} <em style='font-size:8pt;color:#999'>fără TVA</em>"


def _collect_purchase_parts(project: Project, db: Session) -> list[dict]:
    """Return list of {part, quantity} for all parts with requiresPurchase=True in the project."""
    items = project.items or []
    accumulated: dict[str, dict] = {}

    for item in items:
        item_type = item.get("type", "product")
        qty = max(1, int(item.get("quantity", 1)))

        if item_type == "part":
            part_id = item.get("partId")
            if not part_id:
                continue
            if part_id in accumulated:
                accumulated[part_id]["quantity"] += qty
            else:
                part = db.query(Part).filter(Part.id == part_id).first()
                if part and part.requires_purchase:
                    accumulated[part_id] = {"part": part, "quantity": qty}

        elif item_type == "assembly":
            asm_id = item.get("assemblyId")
            if not asm_id:
                continue
            for part, part_qty in iter_assembly_parts(asm_id, db):
                if not part.requires_purchase:
                    continue
                total_qty = int(part_qty) * qty
                if part.id in accumulated:
                    accumulated[part.id]["quantity"] += total_qty
                else:
                    accumulated[part.id] = {"part": part, "quantity": total_qty}

        elif item_type == "product":
            from app.models.product import Product as ProductModel
            product_id = item.get("productId")
            if not product_id:
                continue
            product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
            if not product:
                continue
            # Direct part entries on product
            for pp in (product.product_parts or []):
                p_id = pp.get("partId") if isinstance(pp, dict) else getattr(pp, "part_id", None)
                p_qty = pp.get("quantity", 1) if isinstance(pp, dict) else getattr(pp, "quantity", 1)
                total_qty = int(p_qty) * qty
                part = db.query(Part).filter(Part.id == p_id).first()
                if not part or not part.requires_purchase:
                    continue
                if p_id in accumulated:
                    accumulated[p_id]["quantity"] += total_qty
                else:
                    accumulated[p_id] = {"part": part, "quantity": total_qty}
            # Assembly trees
            for pa in (product.product_assemblies or []):
                a_id = pa.get("assemblyId") if isinstance(pa, dict) else getattr(pa, "assembly_id", None)
                a_qty = pa.get("quantity", 1) if isinstance(pa, dict) else getattr(pa, "quantity", 1)
                for part, part_qty in iter_assembly_parts(a_id, db):
                    if not part.requires_purchase:
                        continue
                    total_qty = int(part_qty) * int(a_qty) * qty
                    if part.id in accumulated:
                        accumulated[part.id]["quantity"] += total_qty
                    else:
                        accumulated[part.id] = {"part": part, "quantity": total_qty}

    return sorted(accumulated.values(), key=lambda x: x["part"].name or "")


def generate_purchase_list_pdf(project: Project, db: Session) -> bytes:
    from weasyprint import HTML

    rows = _collect_purchase_parts(project, db)

    if not rows:
        table_html = "<p style='color:#888;font-style:italic;margin-top:8px'>Nicio piesă marcată pentru achiziție.</p>"
        part_count = 0
        total_qty = 0
    else:
        header = """
        <table>
          <thead>
            <tr>
              <th>Piesă</th>
              <th class="right">Cant.</th>
              <th>Furnizor</th>
              <th>Preț</th>
              <th>Contact agent</th>
            </tr>
          </thead>
          <tbody>
        """
        body_rows = []
        for row in rows:
            part: Part = row["part"]
            qty: int = row["quantity"]
            code_html = f'<span class="code">{part.code}</span>' if part.code else ""
            body_rows.append(ROW_TEMPLATE.format(
                name=part.name or "—",
                code_html=code_html,
                quantity=qty,
                supplier=part.purchase_supplier or "—",
                price_html=_price_html(part),
                contact=part.purchase_agent_contact or "—",
            ))
        table_html = header + "".join(body_rows) + "</tbody></table>"
        part_count = len(rows)
        total_qty = sum(r["quantity"] for r in rows)

    part_label = "piesă" if part_count == 1 else "piese"
    generated_at = datetime.now().strftime("%d.%m.%Y %H:%M")

    html = HTML_TEMPLATE.format(
        project_name=project.name or "—",
        project_code=project.code or "—",
        generated_at=generated_at,
        table_html=table_html,
        part_count=part_count,
        part_label=part_label,
        total_qty=total_qty,
    )

    return HTML(string=html).write_pdf()
