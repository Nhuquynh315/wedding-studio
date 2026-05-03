from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.core.db import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health():
    return {"status": "ok"}


@router.get("/db")
def health_db(db: Session = Depends(get_db)):
    from app.models import User

    count = db.query(User).count()
    return {"status": "ok", "users_count": count}
