from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import math

from app.db.database import get_db
from app.db.models import User
from app.schemas.defect import DefectCreate, DefectResolve, DefectDefer, DefectResponse
from app.schemas.base import PaginatedResponse
from app.core.security import get_current_user
from app.core.permissions import require_maintenance_or_admin
from app.services import defect_service

router = APIRouter(prefix="/defects", tags=["Defects"])


@router.post("", response_model=DefectResponse, status_code=201)
def create(
    data: DefectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Any authenticated user may report
):
    return defect_service.create_defect(db, data, current_user)


@router.get("", response_model=PaginatedResponse[DefectResponse])
def list_defects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items, total = defect_service.list_defects(db, current_user, page, page_size)
    return PaginatedResponse(
        items=items, total=total, page=page,
        page_size=page_size, pages=math.ceil(total / page_size) or 1
    )


@router.get("/{defect_id}", response_model=DefectResponse)
def get_defect(
    defect_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return defect_service.get_defect_or_404(db, defect_id)


@router.patch("/{defect_id}/resolve", response_model=DefectResponse)
def resolve(
    defect_id: int,
    data: DefectResolve = DefectResolve(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_maintenance_or_admin)
):
    return defect_service.resolve_defect(db, defect_id, data, current_user)


@router.patch("/{defect_id}/defer", response_model=DefectResponse)
def defer(
    defect_id: int,
    data: DefectDefer,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_maintenance_or_admin)
):
    return defect_service.defer_defect(db, defect_id, data, current_user)