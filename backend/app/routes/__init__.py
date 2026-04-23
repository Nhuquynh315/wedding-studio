from app.routes.auth import auth_bp
from app.routes.budget import budget_bp
from app.routes.checklist import checklist_bp
from app.routes.guests import guests_bp
from app.routes.seating import seating_bp
from app.routes.settings import settings_bp
from app.routes.vendors import vendors_bp
from app.routes.wedding import wedding_bp

__all__ = [
    "auth_bp",
    "wedding_bp",
    "guests_bp",
    "checklist_bp",
    "budget_bp",
    "vendors_bp",
    "seating_bp",
    "settings_bp",
]
