import uuid
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.quote import Quote

router = APIRouter()


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
    items: list = []
    checklist: list = []
    issues: list = []
    activity: list = []


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
    items: Optional[list] = None
    checklist: Optional[list] = None
    issues: Optional[list] = None
    activity: Optional[list] = None


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
        "items": p.items or [],
        "checklist": p.checklist or [],
        "issues": p.issues or [],
        "activity": p.activity or [],
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


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if db.query(Project).filter(Project.code == body.code).first():
        raise HTTPException(status_code=400, detail="Project code already exists")
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
        items=body.items or [],
        checklist=body.checklist or [],
        issues=body.issues or [],
        activity=body.activity or [],
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
    if body.items is not None:
        p.items = body.items
    if body.checklist is not None:
        p.checklist = body.checklist
    if body.issues is not None:
        p.issues = body.issues
    if body.activity is not None:
        p.activity = body.activity
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
    activity = list(p.activity or [])
    activity.append({
        "id": str(uuid.uuid4()),
        "action": "Issue resolved",
        "user": current_user.name,
        "timestamp": datetime.now().isoformat(),
    })
    p.activity = activity
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

    p = Project(
        code=f"PRJ-{today.year}-{str(project_count).zfill(3)}",
        name=q.name,
        company_id=q.company_id,
        quote_id=q.id,
        status="draft",
        start_date=today.isoformat(),
        deadline=deadline.isoformat(),
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
