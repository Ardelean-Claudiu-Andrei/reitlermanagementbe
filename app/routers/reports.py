from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.services.weekly_report_service import (
    get_available_weeks,
    compute_weekly_report,
    compute_weekly_summaries,
    is_week_available,
)
from app.services.weekly_report_pdf_service import generate_weekly_report_pdf

router = APIRouter()


def _parse_week_start(week_start: str) -> date:
    try:
        parsed = date.fromisoformat(week_start)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid week_start date, expected YYYY-MM-DD")
    if parsed.weekday() != 0:
        raise HTTPException(status_code=400, detail="week_start must be a Monday")
    return parsed


@router.get("/weekly")
def list_weekly_reports(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    weeks = get_available_weeks()
    return {"weeks": compute_weekly_summaries(weeks, db)}


@router.get("/weekly/{week_start}")
def get_weekly_report(
    week_start: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    parsed = _parse_week_start(week_start)
    if not is_week_available(parsed):
        raise HTTPException(status_code=404, detail="Report not yet available")
    return compute_weekly_report(parsed, db)


@router.get("/weekly/{week_start}/export")
def export_weekly_report_pdf(
    week_start: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    parsed = _parse_week_start(week_start)
    if not is_week_available(parsed):
        raise HTTPException(status_code=404, detail="Report not yet available")
    report = compute_weekly_report(parsed, db)
    pdf_bytes = generate_weekly_report_pdf(report)
    filename = f"raport-saptamanal-{week_start}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
