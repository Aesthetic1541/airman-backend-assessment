"""
Defect service.
Critical defects ground the aircraft immediately.
Only maintenance/admin can resolve or defer.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.db.models import Defect, Aircraft, AircraftStatus, DefectStatus, DefectSeverity, User, UserRole
from app.core.errors import NotFoundError, ForbiddenError, ConflictError
from app.core.permissions import assert_same_base, assert_can_manage_defects
from app.services.audit_service import create_audit_log
from app.schemas.defect import DefectCreate, DefectResolve, DefectDefer


def get_defect_or_404(db: Session, defect_id: int) -> Defect:
    d = db.query(Defect).filter(Defect.id == defect_id).first()
    if not d:
        raise NotFoundError("Defect not found")
    return d


def create_defect(db: Session, data: DefectCreate, actor: User) -> Defect:
    aircraft = db.query(Aircraft).filter(Aircraft.id == data.aircraft_id).first()
    if not aircraft:
        raise NotFoundError("Aircraft not found")
    assert_same_base(actor, aircraft.base_id)

    defect = Defect(
        aircraft_id=data.aircraft_id,
        sortie_id=data.sortie_id,
        reported_by=actor.id,
        severity=data.severity,
        description=data.description,
        status=DefectStatus.OPEN,
    )
    db.add(defect)
    db.flush()

    # Critical defects ground the aircraft immediately
    if data.severity == DefectSeverity.CRITICAL:
        old_ac_status = aircraft.status.value
        aircraft.status = AircraftStatus.GROUNDED
        create_audit_log(db, actor, "AIRCRAFT_GROUNDED_BY_DEFECT", "aircraft", aircraft.id,
                         old_value=old_ac_status, new_value="GROUNDED",
                         reason=f"Critical defect #{defect.id}")

    create_audit_log(db, actor, "DEFECT_CREATED", "defect", defect.id,
                     new_value=data.severity.value)
    db.commit()
    db.refresh(defect)
    return defect


def list_defects(db: Session, actor: User, page: int = 1, page_size: int = 20):
    q = db.query(Defect)
    if actor.role != UserRole.ADMIN:
        # Filter by base via aircraft relationship
        q = q.join(Aircraft).filter(Aircraft.base_id == actor.base_id)
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def resolve_defect(db: Session, defect_id: int, data: DefectResolve, actor: User) -> Defect:
    assert_can_manage_defects(actor)
    defect = get_defect_or_404(db, defect_id)
    assert_same_base(actor, defect.aircraft.base_id)

    if defect.status != DefectStatus.OPEN:
        raise ConflictError(f"Cannot resolve defect in status {defect.status.value}")

    old = defect.status.value
    defect.status = DefectStatus.RESOLVED
    defect.resolved_by = actor.id
    defect.resolved_at = datetime.now(timezone.utc)

    create_audit_log(db, actor, "DEFECT_RESOLVED", "defect", defect.id,
                     old_value=old, new_value="RESOLVED",
                     reason=data.resolution_notes)
    db.commit()
    db.refresh(defect)
    return defect


def defer_defect(db: Session, defect_id: int, data: DefectDefer, actor: User) -> Defect:
    assert_can_manage_defects(actor)
    defect = get_defect_or_404(db, defect_id)
    assert_same_base(actor, defect.aircraft.base_id)

    if defect.status != DefectStatus.OPEN:
        raise ConflictError(f"Cannot defer defect in status {defect.status.value}")

    old = defect.status.value
    defect.status = DefectStatus.DEFERRED

    create_audit_log(db, actor, "DEFECT_DEFERRED", "defect", defect.id,
                     old_value=old, new_value="DEFERRED",
                     reason=data.defer_reason)
    db.commit()
    db.refresh(defect)
    return defect