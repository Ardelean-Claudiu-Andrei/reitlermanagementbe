from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

PRODUCT_CATEGORIES = [
    {"value": "silo-interior", "label": "Silo Interior"},
    {"value": "silo-exterior", "label": "Silo Exterior"},
    {"value": "maia", "label": "Maia"},
    {"value": "dissolver", "label": "Dissolver"},
    {"value": "blower", "label": "Blower"},
    {"value": "cyclone-doser", "label": "Cyclone Doser"},
    {"value": "control-panel", "label": "Control Panel"},
    {"value": "other", "label": "Other"},
]


@router.get("")
def list_categories(_: User = Depends(get_current_user)):
    return PRODUCT_CATEGORIES
