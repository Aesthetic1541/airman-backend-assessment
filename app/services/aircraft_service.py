"""
Aircraft service.
Handles status transitions, overlap checks, and defect-driven grounding.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from app.db.models import Aircraft, Sortie, AircraftStatus, SortieStatus, User
from app.core.errors import NotFoundError, ConflictError, ForbiddenError
from app.core.permissions import assert_same_base
from app.services.audit_service import create_audit_log
from app.schemas.aircraft import AircraftCreate


def get_aircraft_or_404(db: Session, aircraft_id: int) -> Aircraft:
    ac = db.query(Aircraft).filter(Aircraft.id == aircraft_id).first()
    if not ac:
        raise NotFoundError("Aircraft not found")
    return ac


def create_aircraft(db: Session, data: AircraftCreate, actor: User) -> Aircraft:
    assert_same_base(actor, data.base_id)
    ac = Aircraft(**data.model_dump())
    db.add(ac)
    db.commit()
    db.refresh(ac)
    create_audit_log(db, actor, "AIRCRAFT_CREATED", "aircraft", ac.id,
                     new_value=ac.registration)
    db.commit()
    return ac


def list_aircraft(db: Session, actor: User, page: int = 1, page_size: int = 20):
    q = db.query(Aircraft)
    if actor.role.value != "ADMIN":
        q = q.filter(Aircraft.base_id == actor.base_id)
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def ground_aircraft(db: Session, aircraft_id: int, actor: User, reason: str = None) -> Aircraft:
    ac = get_aircraft_or_404(db, aircraft_id)
    assert_same_base(actor, ac.base_id)
    old = ac.status.value
    ac.status = AircraftStatus.GROUNDED
    create_audit_log(db, actor, "AIRCRAFT_GROUNDED", "aircraft", ac.id,
                     old_value=old, new_value="GROUNDED", reason=reason)
    db.commit()
    db.refresh(ac)
    return ac


def mark_aircraft_ready(db: Session, aircraft_id: int, actor: User) -> Aircraft:
    """
    Aircraft can only become READY after all OPEN CRITICAL/HIGH defects are
    resolved or deferred.
    """
    from app.db.models import Defect, DefectStatus, DefectSeverity
    ac = get_aircraft_or_404(db, aircraft_id)
    assert_same_base(actor, ac.base_id)

    # Check for blocking defects
    blocking = (
        db.query(Defect)
        .filter(
            Defect.aircraft_id == aircraft_id,
            Defect.status == DefectStatus.OPEN,
            Defect.severity.in_([DefectSeverity.CRITICAL, DefectSeverity.HIGH]),
        )
        .first()
    )
    if blocking:
        raise ConflictError(
            f"Aircraft has open {blocking.severity.value} defect (ID {blocking.id}). "
            "Resolve or defer all critical/high defects before marking ready."
        )

    old = ac.status.value
    ac.status = AircraftStatus.READY
    create_audit_log(db, actor, "AIRCRAFT_READY", "aircraft", ac.id,
                     old_value=old, new_value="READY")
    db.commit()
    db.refresh(ac)
    return ac


def check_aircraft_overlap(db: Session, aircraft_id: int,
                            start: datetime, end: datetime,
                            exclude_sortie_id: int = None):
    """Raise ConflictError if the aircraft is already scheduled in the given window."""
    q = (
        db.query(Sortie)
        .filter(
            Sortie.aircraft_id == aircraft_id,
            Sortie.status.notin_([SortieStatus.CANCELLED, SortieStatus.CLOSED]),
            or_(
                and_(Sortie.scheduled_start <= start, Sortie.scheduled_end > start),
                and_(Sortie.scheduled_start < end, Sortie.scheduled_end >= end),
                and_(Sortie.scheduled_start >= start, Sortie.scheduled_end <= end),
            )
        )
    )
    if exclude_sortie_id:
        q = q.filter(Sortie.id != exclude_sortie_id)
    if q.first():
        raise ConflictError("Aircraft is already assigned to an overlapping sortie")