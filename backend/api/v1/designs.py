from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from api.core.db import get_db
from api.core.deps import require_wedding_access
from api.schemas.design import DesignPublic, GenerateDesignRequest, GeneratedTheme
from api.services import ai_service
from api.services.ai_service import (
    AIServiceUnauthorized,
    AIServiceUnavailable,
    AIServiceUnconfigured,
)

router = APIRouter(prefix="/weddings/{wedding_id}/designs", tags=["designs"])


def _get_design_or_404(db: Session, wedding_id: int, design_id: int):
    from app.models import Design

    design = db.query(Design).filter(Design.id == design_id).first()
    if design is None or design.wedding_id != wedding_id:
        raise HTTPException(status_code=404, detail="Design not found")
    return design


def _to_public(design) -> DesignPublic:
    return DesignPublic(
        id=design.id,
        wedding_id=design.wedding_id,
        design_type=design.design_type,
        theme=GeneratedTheme.model_validate_json(design.html_content),
        created_at=design.created_at.isoformat(),
    )


@router.post("", response_model=DesignPublic, status_code=status.HTTP_201_CREATED)
def generate_design(
    body: GenerateDesignRequest,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import Design

    try:
        theme = ai_service.generate_wedding_theme(**body.model_dump())
    except AIServiceUnconfigured as e:
        raise HTTPException(status_code=503, detail="AI features not configured") from e
    except AIServiceUnauthorized as e:
        raise HTTPException(status_code=503, detail="AI service misconfigured") from e
    except AIServiceUnavailable as e:
        raise HTTPException(status_code=503, detail="AI service temporarily unavailable") from e

    design = Design(
        wedding_id=wedding.id,
        design_type="invitation",
        html_content=theme.model_dump_json(),
    )
    db.add(design)
    db.commit()
    db.refresh(design)
    return _to_public(design)


@router.get("", response_model=list[DesignPublic])
def list_designs(
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import Design

    designs = (
        db.query(Design)
        .filter(Design.wedding_id == wedding.id)
        .order_by(Design.created_at.desc())
        .all()
    )
    return [_to_public(d) for d in designs]


@router.delete("/{design_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_design(
    design_id: int,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    design = _get_design_or_404(db, wedding.id, design_id)
    db.delete(design)
    db.commit()
    return Response(status_code=204)
