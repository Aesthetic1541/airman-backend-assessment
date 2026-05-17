from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
import math

from app.db.database import get_db
from app.db.models import User
from app.schemas.aircraft import AircraftCreate, AircraftResponse, GroundRequest
from app.schemas.base import PaginatedResponse
from app.core.security import get_current_user
from app.core.permissions import require_maintenance_or_admin, require_dispatcher_or_admin
from app.services import aircraft_service

router = APIRouter(prefix="/aircraft", tags=["Aircraft"])


@router.post("", response_model=AircraftResponse, status_code=201)
def create_aircraft(
    data: AircraftCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_maintenance_or_admin)
):
    return aircraft_service.create_aircraft(db, data, current_user)


@router.get("", response_model=PaginatedResponse[AircraftResponse])
def list_aircraft(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items, total = aircraft_service.list_aircraft(db, current_user, page, page_size)
    return PaginatedResponse(
        items=items, total=total, page=page,
        page_size=page_size, pages=math.ceil(total / page_size) or 1
    )


@router.get("/{aircraft_id}", response_model=AircraftResponse)
def get_aircraft(
    aircraft_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ac = aircraft_service.get_aircraft_or_404(db, aircraft_id)
    from app.core.permissions import assert_same_base
    assert_same_base(current_user, ac.base_id)
    return ac


@router.patch("/{aircraft_id}/ground", response_model=AircraftResponse)
def ground_aircraft(
    aircraft_id: int,
    body: GroundRequest = GroundRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_maintenance_or_admin)
):
    return aircraft_service.ground_aircraft(db, aircraft_id, current_user, body.reason)


@router.patch("/{aircraft_id}/ready", response_model=AircraftResponse)
def mark_ready(
    aircraft_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_maintenance_or_admin)
):
    return aircraft_service.mark_aircraft_ready(db, aircraft_id, current_user)