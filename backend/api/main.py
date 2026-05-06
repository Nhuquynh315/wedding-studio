from fastapi import FastAPI

from api.core.config import settings
from api.v1 import auth, budget, checklist, guests, health, vendors, weddings

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(weddings.router, prefix="/api/v1")
app.include_router(guests.router, prefix="/api/v1")
app.include_router(budget.router, prefix="/api/v1")
app.include_router(vendors.router, prefix="/api/v1")
app.include_router(checklist.router, prefix="/api/v1")
