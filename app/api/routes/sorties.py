from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import math

from app.db.database import get_db
from app.db.models import User
from app.schemas.sortie import SortieCreate, SortieResponse, CancelRequest
from app.schemas.base import PaginatedResponse
from app.core.security import get_current_user
from app.core.permissions import require_dispatcher_or_admin
from app.services import sortie_service

router = APIRouter(prefix="/sorties", tags=["Sorties"])


@router.post("", response_model=SortieResponse, status_code=201)
def create_sortie(
    data: SortieCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dispatcher_or_admin)
):
    return sortie_service.create_sortie(db, data, current_user)


@router.get("", response_model=PaginatedResponse[SortieResponse])
def list_sorties(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items, total = sortie_service.list_sorties(db, current_user, page, page_size)
    return PaginatedResponse(
        items=items, total=total, page=page,
        page_size=page_size, pages=math.ceil(total / page_size) or 1
    )


@router.get("/{sortie_id}", response_model=SortieResponse)
def get_sortie(
    sortie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return sortie_service.get_sortie(db, sortie_id, current_user)


@router.patch("/{sortie_id}/release", response_model=SortieResponse)
def release(
    sortie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dispatcher_or_admin)
):
    return sortie_service.release_sortie(db, sortie_id, current_user)


@router.patch("/{sortie_id}/airborne", response_model=SortieResponse)
def airborne(
    sortie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dispatcher_or_admin)
):
    return sortie_service.mark_airborne(db, sortie_id, current_user)


@router.patch("/{sortie_id}/landed", response_model=SortieResponse)
def landed(
    sortie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dispatcher_or_admin)
):
    return sortie_service.mark_landed(db, sortie_id, current_user)


@router.patch("/{sortie_id}/cancel", response_model=SortieResponse)
def cancel(
    sortie_id: int,
    body: CancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dispatcher_or_admin)
):
    return sortie_service.cancel_sortie(db, sortie_id, current_user, body.reason)


@router.patch("/{sortie_id}/close", response_model=SortieResponse)
def close(
    sortie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dispatcher_or_admin)
):
    return sortie_service.close_sortie(db, sortie_id, current_user)