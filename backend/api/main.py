from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import settings
from api.core.errors import install_exception_handlers
from api.v1 import auth, budget, checklist, guests, health, seating, vendors, weddings

app = FastAPI(
    title="Wedding Studio API",
    description=(
        "JSON API backing the Wedding Studio planning app. "
        "Authentication via JWT; all wedding-scoped resources "
        "are gated by ownership checks. "
        "Error responses use RFC 7807 'application/problem+json'."
    ),
    version=settings.version,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    contact={"name": "Wedding Studio"},
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(weddings.router, prefix="/api/v1")
app.include_router(guests.router, prefix="/api/v1")
app.include_router(budget.router, prefix="/api/v1")
app.include_router(vendors.router, prefix="/api/v1")
app.include_router(checklist.router, prefix="/api/v1")
app.include_router(seating.router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

install_exception_handlers(app)
