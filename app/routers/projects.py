import math
import uuid
from datetime import datetime, date, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.quote import Quote

router = APIRouter()

ACTIVITY_PAGE_SIZE = 10


def activity_timestamp_sort_value(entry: object) -> float:
    """Return a float Unix timestamp for sorting an activity entry.

    Always returns a float so mixed timezone-aware / timezone-naive datetimes
    never reach a comparison that Python cannot perform.
    Returns float('-inf') for any malformed or missing value so those entries
    sort after all valid ones without crashing.
    """
    if not isinstance(entry, dict):
        return float("-inf")

    raw = entry.get("timestamp")

    if not isinstance(raw, str) or not raw.strip():
        return float("-inf")

    value = raw.strip()

    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        parsed = datetime.fromisoformat(value)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            parsed = parsed.astimezone(timezone.utc)

        return parsed.timestamp()
    except (TypeError, ValueError, OverflowError):
        return float("-inf")


class PaginatedActivityResponse(BaseModel):
    items: list
    page: int
    pageSize: int
    total: int
    totalPages: int


def _item_kind(item: dict) -> tuple[str, str]:
    """Normalise a project item to (kind, entity_id). Backward-compatible.

    New format:  {"type": "product"|"assembly"|"part", "productId"|"assemblyId"|"partId": "..."}
    Legacy format (no "type"): treated as product via "productId".
    """
    kind = item.get("type", "product")
    if kind == "assembly":
        return "assembly", item.get("assemblyId", "")
    if kind == "part":
        return "part", item.get("partId", "")
    return "product", item.get("productId", "")


def _consolidate_project_items(items: list) -> list:
    """Merge duplicate project items by summing quantities.

    Two items are equivalent when they share type, entity ID, unit price,
    inventory source, and notes. Preserves first-occurrence order.
    Does not mutate the input list.
    """
    seen: dict[tuple, int] = {}
    result: list[dict] = []

    for item in items:
        if not isinstance(item, dict):
            result.append(item)
            continue

        kind, eid = _item_kind(item)
        key = (
            kind,
            eid,
            float(item.get("unitPrice", 0) or 0),
            bool(item.get("fromInventory", False)),
            (item.get("notes", "") or "").strip(),
        )

        try:
            qty = max(1, int(float(item.get("quantity", 1) or 1)))
        except (TypeError, ValueError):
            qty = 1

        if key in seen:
            idx = seen[key]
            merged = dict(result[idx])
            merged["quantity"] = merged.get("quantity", 1) + qty
            result[idx] = merged
        else:
            seen[key] = len(result)
            result.append(dict(item, quantity=qty))

    return result


def _validate_items(items: list, db: Session) -> None:
    from app.models.product import Product
    from app.models.assembly import Assembly
    from app.models.part import Part
    for item in items:
        kind, eid = _item_kind(item)
        if not eid:
            raise HTTPException(status_code=400, detail=f"Item is missing its entity ID (type={kind!r})")
        if kind == "product":
            if not db.query(Product).filter(Product.id == eid).first():
                raise HTTPException(status_code=400, detail=f"Product {eid!r} not found")
        elif kind == "assembly":
            if not db.query(Assembly).filter(Assembly.id == eid).first():
                raise HTTPException(status_code=400, detail=f"Assembly {eid!r} not found")
        elif kind == "part":
            if not db.query(Part).filter(Part.id == eid).first():
                raise HTTPException(status_code=400, detail=f"Part {eid!r} not found")


class ProjectCreate(BaseModel):
    code: str
    name: str
    companyId: Optional[str] = None
    quoteId: Optional[str] = None
    status: str = "draft"
    startDate: str = ""
    deadline: str = ""
    finishDate: Optional[str] = None
    warrantyExpiration: Optional[str] = None
    installationCost: float = 0.0
    finalPrice: Optional[float] = None
    paidAmount: float = 0.0
    items: list = []
    checklist: list = []
    issues: list = []
    activity: list = []
    stepsCompleted: list = []
    stepsTotal: int = 0


class ProjectUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    companyId: Optional[str] = None
    quoteId: Optional[str] = None
    status: Optional[str] = None
    startDate: Optional[str] = None
    deadline: Optional[str] = None
    finishDate: Optional[str] = None
    warrantyExpiration: Optional[str] = None
    installationCost: Optional[float] = None
    finalPrice: Optional[float] = None
    paidAmount: Optional[float] = None
    items: Optional[list] = None
    checklist: Optional[list] = None
    issues: Optional[list] = None
    activity: Optional[list] = None
    stepsCompleted: Optional[list] = None
    stepsTotal: Optional[int] = None


class StatusUpdate(BaseModel):
    status: str


class ChecklistItemBody(BaseModel):
    id: str
    title: str
    done: bool = False
    note: str = ""
    doneAt: Optional[str] = None


class IssueBody(BaseModel):
    id: str
    description: str
    solved: bool = False
    solvedAt: Optional[str] = None
    createdAt: str


class CreateFromQuoteBody(BaseModel):
    quoteId: str
    userName: str = "System"


def project_to_dict(p: Project) -> dict:
    return {
        "id": p.id,
        "code": p.code,
        "name": p.name,
        "companyId": p.company_id,
        "quoteId": p.quote_id,
        "status": p.status,
        "startDate": p.start_date or "",
        "deadline": p.deadline or "",
        "finishDate": p.finish_date,
        "warrantyExpiration": p.warranty_expiration,
        "installationCost": p.installation_cost or 0.0,
        "finalPrice": p.final_price,
        "paidAmount": p.paid_amount or 0.0,
        "items": p.items or [],
        "checklist": p.checklist or [],
        "issues": p.issues or [],
        "activity": p.activity or [],
        "stepsCompleted": p.steps_completed or [],
        "stepsTotal": p.steps_total or 0,
        "createdAt": p.created_at.isoformat() if p.created_at else None,
        "updatedAt": p.updated_at.isoformat() if p.updated_at else None,
    }


@router.get("")
def list_projects(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return [project_to_dict(p) for p in projects]


@router.get("/{project_id}")
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_to_dict(p)


@router.get("/{project_id}/activity", response_model=PaginatedActivityResponse)
def get_project_activity(
    project_id: str,
    page: int = Query(default=1, ge=1),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    raw_activity = list(p.activity or [])

    # Sort descending: newest first. Use original array index as a secondary
    # tiebreaker (higher index = more recently appended = should appear first).
    indexed = list(enumerate(raw_activity))
    indexed.sort(
        key=lambda pair: (activity_timestamp_sort_value(pair[1]), pair[0]),
        reverse=True,
    )
    sorted_items = [entry for _, entry in indexed]

    total = len(sorted_items)
    total_pages = max(1, math.ceil(total / ACTIVITY_PAGE_SIZE))
    safe_page = min(page, total_pages)

    start = (safe_page - 1) * ACTIVITY_PAGE_SIZE
    end = start + ACTIVITY_PAGE_SIZE
    page_items = sorted_items[start:end]

    return PaginatedActivityResponse(
        items=page_items,
        page=safe_page,
        pageSize=ACTIVITY_PAGE_SIZE,
        total=total,
        totalPages=total_pages,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if db.query(Project).filter(Project.code == body.code).first():
        raise HTTPException(status_code=400, detail="Project code already exists")
    if body.items:
        _validate_items(body.items, db)
    p = Project(
        code=body.code,
        name=body.name,
        company_id=body.companyId,
        quote_id=body.quoteId,
        status=body.status,
        start_date=body.startDate,
        deadline=body.deadline,
        finish_date=body.finishDate,
        warranty_expiration=body.warrantyExpiration,
        installation_cost=body.installationCost or 0.0,
        final_price=body.finalPrice,
        paid_amount=body.paidAmount or 0.0,
        items=body.items or [],
        checklist=body.checklist or [],
        issues=body.issues or [],
        activity=body.activity or [],
        steps_completed=body.stepsCompleted or [],
        steps_total=body.stepsTotal or 0,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return project_to_dict(p)


@router.put("/{project_id}")
def update_project(
    project_id: str,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    if body.code is not None:
        p.code = body.code
    if body.name is not None:
        p.name = body.name
    if body.companyId is not None:
        p.company_id = body.companyId
    if body.quoteId is not None:
        p.quote_id = body.quoteId
    if body.status is not None:
        p.status = body.status
    if body.startDate is not None:
        p.start_date = body.startDate
    if body.deadline is not None:
        p.deadline = body.deadline
    if body.finishDate is not None:
        p.finish_date = body.finishDate
    if body.warrantyExpiration is not None:
        p.warranty_expiration = body.warrantyExpiration
    if body.installationCost is not None:
        p.installation_cost = body.installationCost
    if body.finalPrice is not None:
        p.final_price = body.finalPrice
    if body.paidAmount is not None:
        p.paid_amount = body.paidAmount
    if body.items is not None:
        consolidated = _consolidate_project_items(body.items)
        _validate_items(consolidated, db)
        p.items = consolidated
    if body.checklist is not None:
        p.checklist = body.checklist
    if body.issues is not None:
        p.issues = body.issues
    if body.activity is not None:
        p.activity = body.activity
    if body.stepsCompleted is not None:
        p.steps_completed = body.stepsCompleted
        flag_modified(p, "steps_completed")
    if body.stepsTotal is not None:
        p.steps_total = body.stepsTotal
    db.commit()
    db.refresh(p)
    return project_to_dict(p)


@router.patch("/{project_id}/status")
def update_project_status(
    project_id: str,
    body: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    p.status = body.status
    activity = list(p.activity or [])
    activity.append({
        "id": str(uuid.uuid4()),
        "action": f"Status changed to {body.status.replace('-', ' ')}",
        "user": current_user.name,
        "timestamp": datetime.now().isoformat(),
    })
    p.activity = activity
    db.commit()
    db.refresh(p)
    return project_to_dict(p)


@router.post("/{project_id}/finish")
def finish_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    today = date.today().isoformat()
    warranty = date(date.today().year + 2, date.today().month, date.today().day).isoformat()
    p.status = "done"
    p.finish_date = today
    p.warranty_expiration = warranty
    activity = list(p.activity or [])
    activity.append({
        "id": str(uuid.uuid4()),
        "action": "Project finished",
        "user": current_user.name,
        "timestamp": datetime.now().isoformat(),
    })
    p.activity = activity
    db.commit()
    db.refresh(p)
    return project_to_dict(p)


@router.post("/{project_id}/checklist")
def add_checklist_item(
    project_id: str,
    body: ChecklistItemBody,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    checklist = list(p.checklist or [])
    checklist.append(body.model_dump())
    p.checklist = checklist
    flag_modified(p, "checklist")
    db.commit()
    db.refresh(p)
    return project_to_dict(p)


@router.patch("/{project_id}/checklist/{item_id}/toggle")
def toggle_checklist_item(
    project_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    checklist = list(p.checklist or [])
    today = date.today().isoformat()
    for item in checklist:
        if item.get("id") == item_id:
            item["done"] = not item.get("done", False)
            item["doneAt"] = today if item["done"] else None
            break
    p.checklist = checklist
    flag_modified(p, "checklist")
    db.commit()
    db.refresh(p)
    return project_to_dict(p)


@router.post("/{project_id}/issues")
def add_project_issue(
    project_id: str,
    body: IssueBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    issues = list(p.issues or [])
    issues.append(body.model_dump())
    p.issues = issues
    activity = list(p.activity or [])
    activity.append({
        "id": str(uuid.uuid4()),
        "action": f"Issue reported: {body.description[:50]}",
        "user": current_user.name,
        "timestamp": datetime.now().isoformat(),
    })
    p.activity = activity
    db.commit()
    db.refresh(p)
    return project_to_dict(p)


@router.patch("/{project_id}/issues/{issue_id}/resolve")
def resolve_issue(
    project_id: str,
    issue_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    issues = list(p.issues or [])
    today = date.today().isoformat()
    for issue in issues:
        if issue.get("id") == issue_id:
            issue["solved"] = True
            issue["solvedAt"] = today
            break
    p.issues = issues
    flag_modified(p, "issues")
    activity = list(p.activity or [])
    activity.append({
        "id": str(uuid.uuid4()),
        "action": "Issue resolved",
        "user": current_user.name,
        "timestamp": datetime.now().isoformat(),
    })
    p.activity = activity
    flag_modified(p, "activity")
    db.commit()
    db.refresh(p)
    return project_to_dict(p)


@router.post("/from-quote", status_code=status.HTTP_201_CREATED)
def create_project_from_quote(
    body: CreateFromQuoteBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Quote).filter(Quote.id == body.quoteId).first()
    if not q:
        raise HTTPException(status_code=404, detail="Quote not found")

    project_count = db.query(Project).count() + 1
    today = date.today()
    deadline = date(
        today.year + (1 if today.month + (q.delivery_time_weeks * 7 // 30) > 12 else 0),
        ((today.month + (q.delivery_time_weeks * 7 // 30) - 1) % 12) + 1,
        today.day,
    )

    items = [
        {
            "productId": item.get("productId"),
            "quantity": item.get("quantity"),
            "unitPrice": item.get("unitPrice"),
            "notes": item.get("notes", ""),
            "fromInventory": False,
        }
        for item in (q.items or [])
    ]

    quote_subtotal = sum(
        item.get("unitPrice", 0) * item.get("quantity", 0)
        for item in (q.items or [])
    )
    quote_total = quote_subtotal + (q.installation or 0.0)

    p = Project(
        code=f"PRJ-{today.year}-{str(project_count).zfill(3)}",
        name=q.name,
        company_id=q.company_id,
        quote_id=q.id,
        status="draft",
        start_date=today.isoformat(),
        deadline=deadline.isoformat(),
        installation_cost=q.installation or 0.0,
        final_price=quote_total,
        items=items,
        checklist=[],
        issues=[],
        activity=[{
            "id": str(uuid.uuid4()),
            "action": "Project created from quote",
            "user": current_user.name,
            "timestamp": datetime.now().isoformat(),
        }],
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return project_to_dict(p)


class StepToggleBody(BaseModel):
    stepKey: str
    stepsTotal: Optional[int] = None


@router.patch("/{project_id}/steps/toggle")
def toggle_step(
    project_id: str,
    body: StepToggleBody,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    steps = list(p.steps_completed or [])
    if body.stepKey in steps:
        steps.remove(body.stepKey)
    else:
        steps.append(body.stepKey)

    p.steps_completed = steps
    flag_modified(p, "steps_completed")

    if body.stepsTotal is not None:
        p.steps_total = body.stepsTotal

    db.commit()
    db.refresh(p)
    return {"stepsCompleted": p.steps_completed, "stepsTotal": p.steps_total or 0}


@router.get("/{project_id}/export-production-steps")
def export_project_production_steps_pdf(
    project_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.services.steps_pdf_service import generate_project_steps_pdf
    pdf_bytes = generate_project_steps_pdf(p, db)

    filename = f"pasi-productie-{p.code}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{project_id}/export-laser-cutting")
def export_project_laser_cutting_pdf(
    project_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.services.laser_cutting_pdf_service import generate_project_laser_cutting_pdf
    pdf_bytes = generate_project_laser_cutting_pdf(p, db)

    filename = f"taiere-laser-{p.code}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{project_id}/export-production-cards")
def export_project_production_cards_pdf(
    project_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.services.production_cards_pdf_service import generate_production_cards_pdf
    pdf_bytes = generate_production_cards_pdf(p, db)

    filename = f"fise-productie-{p.code}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(p)
    db.commit()
