"""
Sortie service.
Enforces the full sortie state machine and all aircraft readiness rules.

Valid transitions:
  SCHEDULED → RELEASED → AIRBORNE → LANDED → TRAINING_SUBMITTED
  → TRAINING_APPROVED → CLOSED

All other transitions are rejected with INVALID_STATE_TRANSITION.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.db.models import (
    Sortie, Aircraft, User, AircraftStatus, SortieStatus, UserRole
)
from app.core.errors import NotFoundError, InvalidTransitionError, ConflictError, ForbiddenError
from app.core.permissions import assert_same_base, assert_can_manage_sortie_workflow, assert_can_view_sortie
from app.services.audit_service import create_audit_log
from app.services.aircraft_service import check_aircraft_overlap
from app.schemas.sortie import SortieCreate


VALID_TRANSITIONS = {
    SortieStatus.SCHEDULED: [SortieStatus.RELEASED, SortieStatus.CANCELLED],
    SortieStatus.RELEASED: [SortieStatus.AIRBORNE, SortieStatus.CANCELLED],
    SortieStatus.AIRBORNE: [SortieStatus.LANDED],
    SortieStatus.LANDED: [SortieStatus.TRAINING_SUBMITTED, SortieStatus.RECOVERY_REQUIRED],
    SortieStatus.TRAINING_SUBMITTED: [SortieStatus.TRAINING_APPROVED],
    SortieStatus.TRAINING_APPROVED: [SortieStatus.CLOSED],
    SortieStatus.AIRCRAFT_GROUNDED: [SortieStatus.RECOVERY_REQUIRED],
    # Terminal states — no further transitions
    SortieStatus.CLOSED: [],
    SortieStatus.CANCELLED: [],
    SortieStatus.RECOVERY_REQUIRED: [],
}


def _assert_transition(sortie: Sortie, target: SortieStatus):
    allowed = VALID_TRANSITIONS.get(sortie.status, [])
    if target not in allowed:
        raise InvalidTransitionError(sortie.status.value, target.value)


def get_sortie_or_404(db: Session, sortie_id: int) -> Sortie:
    s = db.query(Sortie).filter(Sortie.id == sortie_id).first()
    if not s:
        raise NotFoundError("Sortie not found")
    return s


def create_sortie(db: Session, data: SortieCreate, actor: User) -> Sortie:
    assert_can_manage_sortie_workflow(actor)
    assert_same_base(actor, data.base_id)

    # Validate aircraft availability
    aircraft = db.query(Aircraft).filter(Aircraft.id == data.aircraft_id).first()
    if not aircraft:
        raise NotFoundError("Aircraft not found")
    if aircraft.status == AircraftStatus.GROUNDED:
        raise ConflictError("Grounded aircraft cannot be assigned to a new sortie")
    if aircraft.base_id != data.base_id:
        raise ConflictError("Aircraft does not belong to the same base as the sortie")

    check_aircraft_overlap(db, data.aircraft_id, data.scheduled_start, data.scheduled_end)

    sortie = Sortie(**data.model_dump())
    db.add(sortie)
    # Mark aircraft as SCHEDULED
    aircraft.status = AircraftStatus.SCHEDULED
    db.flush()

    create_audit_log(db, actor, "SORTIE_CREATED", "sortie", sortie.id,
                     new_value=SortieStatus.SCHEDULED.value)
    db.commit()
    db.refresh(sortie)
    return sortie


def list_sorties(db: Session, actor: User, page: int = 1, page_size: int = 20):
    q = db.query(Sortie)
    role = actor.role
    if role == UserRole.CADET:
        q = q.filter(Sortie.cadet_id == actor.id)
    elif role == UserRole.INSTRUCTOR:
        q = q.filter(Sortie.instructor_id == actor.id)
    elif role != UserRole.ADMIN:
        q = q.filter(Sortie.base_id == actor.base_id)
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_sortie(db: Session, sortie_id: int, actor: User) -> Sortie:
    sortie = get_sortie_or_404(db, sortie_id)
    assert_can_view_sortie(actor, sortie)
    return sortie


def release_sortie(db: Session, sortie_id: int, actor: User) -> Sortie:
    sortie = get_sortie_or_404(db, sortie_id)
    assert_can_manage_sortie_workflow(actor)
    assert_same_base(actor, sortie.base_id)

    aircraft = sortie.aircraft
    if aircraft.status == AircraftStatus.GROUNDED:
        raise ConflictError("Grounded aircraft cannot be released for sortie")

    _assert_transition(sortie, SortieStatus.RELEASED)
    old = sortie.status.value
    sortie.status = SortieStatus.RELEASED
    create_audit_log(db, actor, "SORTIE_RELEASED", "sortie", sortie.id,
                     old_value=old, new_value="RELEASED")
    db.commit()
    db.refresh(sortie)
    return sortie


def mark_airborne(db: Session, sortie_id: int, actor: User) -> Sortie:
    sortie = get_sortie_or_404(db, sortie_id)
    assert_can_manage_sortie_workflow(actor)
    assert_same_base(actor, sortie.base_id)

    _assert_transition(sortie, SortieStatus.AIRBORNE)
    old_sortie = sortie.status.value
    sortie.status = SortieStatus.AIRBORNE
    sortie.actual_start = datetime.now(timezone.utc)

    # Aircraft mirrors sortie status
    sortie.aircraft.status = AircraftStatus.AIRBORNE
    create_audit_log(db, actor, "SORTIE_AIRBORNE", "sortie", sortie.id,
                     old_value=old_sortie, new_value="AIRBORNE")
    db.commit()
    db.refresh(sortie)
    return sortie


def mark_landed(db: Session, sortie_id: int, actor: User) -> Sortie:
    sortie = get_sortie_or_404(db, sortie_id)
    assert_can_manage_sortie_workflow(actor)
    assert_same_base(actor, sortie.base_id)

    _assert_transition(sortie, SortieStatus.LANDED)
    old = sortie.status.value
    sortie.status = SortieStatus.LANDED
    sortie.actual_end = datetime.now(timezone.utc)
    sortie.aircraft.status = AircraftStatus.LANDED
    create_audit_log(db, actor, "SORTIE_LANDED", "sortie", sortie.id,
                     old_value=old, new_value="LANDED")
    db.commit()
    db.refresh(sortie)
    return sortie


def cancel_sortie(db: Session, sortie_id: int, actor: User, reason: str) -> Sortie:
    sortie = get_sortie_or_404(db, sortie_id)
    assert_can_manage_sortie_workflow(actor)
    assert_same_base(actor, sortie.base_id)

    _assert_transition(sortie, SortieStatus.CANCELLED)
    old = sortie.status.value
    sortie.status = SortieStatus.CANCELLED
    sortie.cancel_reason = reason
    # Free up the aircraft
    if sortie.aircraft.status in (AircraftStatus.SCHEDULED,):
        sortie.aircraft.status = AircraftStatus.READY
    create_audit_log(db, actor, "SORTIE_CANCELLED", "sortie", sortie.id,
                     old_value=old, new_value="CANCELLED", reason=reason)
    db.commit()
    db.refresh(sortie)
    return sortie


def close_sortie(db: Session, sortie_id: int, actor: User) -> Sortie:
    """
    Closing requires training to be APPROVED first.
    The sortie must also not have any unresolved grounding situation.
    """
    from app.db.models import TrainingStatus
    sortie = get_sortie_or_404(db, sortie_id)
    assert_can_manage_sortie_workflow(actor)
    assert_same_base(actor, sortie.base_id)

    _assert_transition(sortie, SortieStatus.CLOSED)

    # Training must be approved before close
    tp = sortie.training_progress
    if not tp or tp.status != TrainingStatus.APPROVED:
        raise ConflictError("Sortie cannot be closed before training progress is approved")

    old = sortie.status.value
    sortie.status = SortieStatus.CLOSED
    if sortie.aircraft.status == AircraftStatus.LANDED:
        sortie.aircraft.status = AircraftStatus.READY
    create_audit_log(db, actor, "SORTIE_CLOSED", "sortie", sortie.id,
                     old_value=old, new_value="CLOSED")
    db.commit()
    db.refresh(sortie)
    return sortie