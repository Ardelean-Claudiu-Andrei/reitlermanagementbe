from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.client import Client
from app.models.quote import Quote
from app.models.project import Project

router = APIRouter()


@router.get("")
def get_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    total_products = db.query(Product).filter(Product.is_active == True).count()
    total_clients = db.query(Client).count()
    total_quotes = db.query(Quote).count()
    total_projects = db.query(Project).count()

    active_projects = db.query(Project).filter(Project.status == "in-progress").count()
    approved_quotes = db.query(Quote).filter(Quote.status == "approved").count()
    draft_quotes = db.query(Quote).filter(Quote.status == "draft").count()
    done_projects = db.query(Project).filter(Project.status == "done").count()

    return {
        "totalProducts": total_products,
        "totalClients": total_clients,
        "totalQuotes": total_quotes,
        "totalProjects": total_projects,
        "activeProjects": active_projects,
        "approvedQuotes": approved_quotes,
        "draftQuotes": draft_quotes,
        "doneProjects": done_projects,
    }
