"""PDF rendering for the weekly activity report (admin Dashboard feature)."""

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: A4; margin: 15mm; }
body { font-family: Arial, sans-serif; font-size: 10pt; color: #111; }

h1 { font-size: 18pt; margin-bottom: 2mm; }
.subtitle { font-size: 10pt; color: #555; margin-bottom: 8mm; }

.section-title {
  font-size: 11pt;
  font-weight: bold;
  background: #111;
  color: #fff;
  padding: 4px 8px;
  margin-top: 8mm;
  margin-bottom: 3mm;
}

table { width: 100%; border-collapse: collapse; margin-bottom: 2mm; }
th {
  text-align: left;
  font-size: 7.5pt;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: #555;
  border-bottom: 1.5px solid #111;
  padding: 4px 6px;
}
td { font-size: 9pt; border-bottom: 1px solid #ddd; padding: 4px 6px; }
tr:last-child td { border-bottom: none; }

.empty { color: #999; font-style: italic; font-size: 9pt; padding: 6px 2px; }
.status-badge {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 7.5pt;
  background: #eee;
  color: #333;
}
.code { font-family: monospace; font-size: 8.5pt; color: #444; }
"""

_HTML_WRAPPER = """<!DOCTYPE html>
<html lang="ro">
<head><meta charset="UTF-8"/><style>{css}</style></head>
<body>
  <h1>Raport săptămânal de activitate</h1>
  <div class="subtitle">{week_start} — {week_end} &nbsp;·&nbsp; Generat: {generated_at}</div>

  <div class="section-title">Proiecte cu progres săptămâna aceasta ({progressed_count})</div>
  {progressed_table}

  <div class="section-title">Proiecte finalizate ({finalized_count})</div>
  {finalized_table}

  <div class="section-title">Proiecte în lucru ({in_progress_count})</div>
  {in_progress_table}

  <div class="section-title">Proiecte care urmează să înceapă săptămâna viitoare ({starting_next_week_count})</div>
  {starting_next_week_table}
</body>
</html>"""


def _fmt_date(iso: str) -> str:
    return iso[:10] if iso else ""


def _fmt_datetime(iso: str) -> str:
    if not iso:
        return ""
    return iso[:16].replace("T", " ")


def _progressed_table(items: list[dict]) -> str:
    if not items:
        return '<div class="empty">Niciun proiect cu activitate în această săptămână.</div>'
    rows = "".join(
        f'<tr><td class="code">{it["code"]}</td><td>{it["name"]}</td><td>{it["companyName"] or "—"}</td>'
        f'<td><span class="status-badge">{it["status"]}</span></td><td>{it["progressPct"]}%</td>'
        f'<td>{it["lastAction"]}</td><td>{_fmt_datetime(it["lastActionAt"])}</td></tr>'
        for it in items
    )
    return (
        '<table><thead><tr><th>Cod</th><th>Proiect</th><th>Client</th><th>Status</th>'
        '<th>Progres</th><th>Ultima acțiune</th><th>Când</th></tr></thead>'
        f'<tbody>{rows}</tbody></table>'
    )


def _change_table(items: list[dict], empty_msg: str) -> str:
    if not items:
        return f'<div class="empty">{empty_msg}</div>'
    rows = "".join(
        f'<tr><td class="code">{it["code"]}</td><td>{it["name"]}</td><td>{it["companyName"] or "—"}</td>'
        f'<td>{it["change"]}</td><td>{_fmt_datetime(it["changedAt"])}</td></tr>'
        for it in items
    )
    return (
        '<table><thead><tr><th>Cod</th><th>Proiect</th><th>Client</th>'
        '<th>Schimbare</th><th>Când</th></tr></thead>'
        f'<tbody>{rows}</tbody></table>'
    )


def _status_table(items: list[dict], empty_msg: str) -> str:
    if not items:
        return f'<div class="empty">{empty_msg}</div>'
    rows = "".join(
        f'<tr><td class="code">{it["code"]}</td><td>{it["name"]}</td><td>{it["companyName"] or "—"}</td>'
        f'<td><span class="status-badge">{it["status"]}</span></td><td>{it["progressPct"]}%</td></tr>'
        for it in items
    )
    return (
        '<table><thead><tr><th>Cod</th><th>Proiect</th><th>Client</th>'
        '<th>Status</th><th>Progres</th></tr></thead>'
        f'<tbody>{rows}</tbody></table>'
    )


def _starting_next_week_table(items: list[dict]) -> str:
    if not items:
        return '<div class="empty">Niciun proiect programat să înceapă săptămâna viitoare.</div>'
    rows = "".join(
        f'<tr><td class="code">{it["code"]}</td><td>{it["name"]}</td><td>{it["companyName"] or "—"}</td>'
        f'<td><span class="status-badge">{it["status"]}</span></td><td>{_fmt_date(it["startDate"])}</td></tr>'
        for it in items
    )
    return (
        '<table><thead><tr><th>Cod</th><th>Proiect</th><th>Client</th>'
        '<th>Status</th><th>Dată început</th></tr></thead>'
        f'<tbody>{rows}</tbody></table>'
    )


def generate_weekly_report_pdf(report: dict) -> bytes:
    from weasyprint import HTML

    html = _HTML_WRAPPER.format(
        css=_CSS,
        week_start=_fmt_date(report["weekStart"]),
        week_end=_fmt_date(report["weekEnd"]),
        generated_at=_fmt_datetime(report["generatedAt"]),
        progressed_count=len(report["progressedProjects"]),
        finalized_count=len(report["finalizedProjects"]),
        in_progress_count=len(report["inProgressProjects"]),
        starting_next_week_count=len(report["startingNextWeekProjects"]),
        progressed_table=_progressed_table(report["progressedProjects"]),
        finalized_table=_change_table(report["finalizedProjects"], "Niciun proiect finalizat în această săptămână."),
        in_progress_table=_status_table(report["inProgressProjects"], "Niciun proiect în lucru."),
        starting_next_week_table=_starting_next_week_table(report["startingNextWeekProjects"]),
    )
    return HTML(string=html).write_pdf()
