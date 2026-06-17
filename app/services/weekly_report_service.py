"""
Weekly activity report computation.

A "week" is the business week Monday → Friday. The report for a given week
becomes available the moment that week's Friday 17:00 passes — at that point
all Mon-Fri activity is final and the report is considered closed. Anything
logged after Friday 17:00 (Friday evening / weekend) rolls into next week's
report.

No persistence: reports are computed on demand from current project data,
the same pattern used by the other PDF/JSON exports in this codebase.
"""

from datetime import date, datetime, time, timedelta
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.client import Client

REPORT_HOUR = 17  # Friday cutoff hour
_FINALIZED_EXACT = {"Project finished", "Status changed to done"}


def _monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _week_bounds(week_start: date) -> tuple[date, date, datetime]:
    """week_start must be a Monday. Returns (week_start, week_end_friday, available_at)."""
    week_end = week_start + timedelta(days=4)
    available_at = datetime.combine(week_end, time(REPORT_HOUR, 0))
    return week_start, week_end, available_at


def is_week_available(week_start: date) -> bool:
    _, _, available_at = _week_bounds(week_start)
    return available_at <= datetime.now()


def get_available_weeks(limit: int = 12) -> list[dict]:
    """Most recent `limit` weeks whose Friday-17:00 cutoff has already passed."""
    now = datetime.now()
    monday = _monday_of(now.date())
    _, _, available_at = _week_bounds(monday)
    if available_at > now:
        monday -= timedelta(days=7)

    weeks = []
    for _ in range(limit):
        week_start, week_end, available_at = _week_bounds(monday)
        weeks.append({
            "weekStart": week_start.isoformat(),
            "weekEnd": week_end.isoformat(),
            "availableAt": available_at.isoformat(),
        })
        monday -= timedelta(days=7)
    return weeks


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        parsed = datetime.fromisoformat(ts)
    except ValueError:
        return None
    return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed


def _is_finalized_change(action: str) -> bool:
    return action in _FINALIZED_EXACT


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def load_projects_with_companies(db: Session) -> tuple[list[Project], dict[str, str]]:
    """Fetch all projects + a companyId→name lookup once, reused across multiple weeks."""
    projects = db.query(Project).all()
    company_ids = {p.company_id for p in projects if p.company_id}
    companies_by_id = {
        c.id: c.name for c in (db.query(Client).filter(Client.id.in_(company_ids)).all() if company_ids else [])
    }
    return projects, companies_by_id


def build_report(projects: list[Project], companies_by_id: dict[str, str], week_start: date) -> dict:
    week_start, week_end, window_end = _week_bounds(week_start)
    window_start = datetime.combine(week_start, time(0, 0))
    next_week_start = week_start + timedelta(days=7)
    next_week_end = week_start + timedelta(days=11)

    progressed: list[dict] = []
    finalized: list[dict] = []
    in_progress: list[dict] = []
    starting_next_week: list[dict] = []

    for p in projects:
        company_name = companies_by_id.get(p.company_id, "") if p.company_id else ""
        steps_total = p.steps_total or 0
        steps_done = len(p.steps_completed or [])
        progress_pct = round((steps_done / steps_total) * 100) if steps_total else 0

        if p.status == "in-progress":
            in_progress.append({
                "id": p.id, "code": p.code, "name": p.name, "status": p.status,
                "companyName": company_name, "progressPct": progress_pct,
            })

        start_date = _parse_date(p.start_date)
        if start_date and next_week_start <= start_date <= next_week_end and p.status not in ("done", "cancelled"):
            starting_next_week.append({
                "id": p.id, "code": p.code, "name": p.name, "status": p.status,
                "companyName": company_name, "startDate": p.start_date,
            })

        activity_in_week = [
            a for a in (p.activity or [])
            if (ts := _parse_ts(a.get("timestamp"))) and window_start <= ts <= window_end
        ]
        updated_at = p.updated_at.replace(tzinfo=None) if p.updated_at else None
        updated_in_window = bool(updated_at and window_start <= updated_at <= window_end)

        if activity_in_week or updated_in_window:
            if activity_in_week:
                last_action = activity_in_week[-1]["action"]
                last_action_at = activity_in_week[-1]["timestamp"]
            else:
                last_action = "Actualizat"
                last_action_at = updated_at.isoformat() if updated_at else ""
            progressed.append({
                "id": p.id, "code": p.code, "name": p.name, "status": p.status,
                "companyName": company_name, "progressPct": progress_pct,
                "lastAction": last_action, "lastActionAt": last_action_at,
            })

        finalized_changes = [a for a in activity_in_week if _is_finalized_change(a.get("action", ""))]
        if finalized_changes:
            latest = finalized_changes[-1]
            finalized.append({
                "id": p.id, "code": p.code, "name": p.name, "status": p.status,
                "companyName": company_name,
                "change": latest["action"], "changedAt": latest["timestamp"],
            })

    return {
        "weekStart": week_start.isoformat(),
        "weekEnd": week_end.isoformat(),
        "generatedAt": datetime.now().isoformat(),
        "progressedProjects": progressed,
        "finalizedProjects": finalized,
        "inProgressProjects": in_progress,
        "startingNextWeekProjects": starting_next_week,
    }


def compute_weekly_report(week_start: date, db: Session) -> dict:
    projects, companies_by_id = load_projects_with_companies(db)
    return build_report(projects, companies_by_id, week_start)


def compute_weekly_summaries(weeks: list[dict], db: Session) -> list[dict]:
    """Builds list-view summaries for several weeks from a single DB fetch."""
    projects, companies_by_id = load_projects_with_companies(db)
    summaries = []
    for w in weeks:
        report = build_report(projects, companies_by_id, date.fromisoformat(w["weekStart"]))
        summaries.append({
            **w,
            "progressedCount": len(report["progressedProjects"]),
            "finalizedCount": len(report["finalizedProjects"]),
        })
    return summaries
