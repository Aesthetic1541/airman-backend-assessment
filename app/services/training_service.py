"""
Training progress service.
Rules:
  - Only assigned instructor can create/submit.
  - Only CFI can approve/reject.
  - Cadet cannot touch training records.
  - Scores must be 1-5.
  - Remarks required on submission.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.db.models import TrainingProgress, Sortie, User, TrainingStatus, SortieStatus, UserRole
from app.core.errors import NotFoundError, ForbiddenError, ConflictError, ValidationError
from app.core.permissions import assert_can_submit_training, assert_can_approve_training
from app.services.audit_service import create_audit_log
from app.schemas.training_progress import TrainingCreate, TrainingSubmit, TrainingReject


def get_tp_or_404(db: Session, tp_id: int) -> TrainingProgress:
    tp = db.query(TrainingProgress).filter(TrainingProgress.id == tp_id).first()
    if not tp:
        raise NotFoundError("Training progress record not found")
    return tp


def create_training(db: Session, data: TrainingCreate, actor: User) -> TrainingProgress:
    sortie = db.query(Sortie).filter(Sortie.id == data.sortie_id).first()
    if not sortie:
        raise NotFoundError("Sortie not found")

    # Cadet may never create
    if actor.role == UserRole.CADET:
        raise ForbiddenError("Cadets cannot create training progress records")

    assert_can_submit_training(actor, sortie.instructor_id)

    # One-to-one: reject duplicate
    existing = db.query(TrainingProgress).filter(TrainingProgress.sortie_id == data.sortie_id).first()
    if existing:
        raise ConflictError("Training progress already exists for this sortie")

    tp = TrainingProgress(
        sortie_id=data.sortie_id,
        cadet_id=sortie.cadet_id,
        instructor_id=sortie.instructor_id,
        lesson_type=data.lesson_type,
        status=TrainingStatus.DRAFT,
    )
    db.add(tp)
    db.commit()
    db.refresh(tp)
    return tp


def get_training_by_sortie(db: Session, sortie_id: int, actor: User) -> TrainingProgress:
    sortie = db.query(Sortie).filter(Sortie.id == sortie_id).first()
    if not sortie:
        raise NotFoundError("Sortie not found")

    tp = db.query(TrainingProgress).filter(TrainingProgress.sortie_id == sortie_id).first()
    if not tp:
        raise NotFoundError("No training record for this sortie")

    # Cadets only see APPROVED records
    if actor.role == UserRole.CADET:
        if tp.cadet_id != actor.id:
            raise ForbiddenError("Access denied")
        if tp.status != TrainingStatus.APPROVED:
            raise ForbiddenError("Training progress is not yet approved")

    return tp


def submit_training(db: Session, tp_id: int, data: TrainingSubmit, actor: User) -> TrainingProgress:
    tp = get_tp_or_404(db, tp_id)
    assert_can_submit_training(actor, tp.instructor_id)

    if tp.status != TrainingStatus.DRAFT:
        raise ConflictError(f"Cannot submit training in status {tp.status.value}")

    # Pydantic already validates scores and remarks, but double-check defensively
    for field in ("maneuver_score", "communication_score", "situational_awareness_score"):
        v = getattr(data, field)
        if not isinstance(v, int) or not (1 <= v <= 5):
            raise ValidationError(f"Score must be between 1 and 5", field)

    old = tp.status.value
    tp.maneuver_score = data.maneuver_score
    tp.communication_score = data.communication_score
    tp.situational_awareness_score = data.situational_awareness_score
    tp.remarks = data.remarks
    tp.status = TrainingStatus.SUBMITTED
    tp.submitted_at = datetime.now(timezone.utc)

    # Advance sortie status to TRAINING_SUBMITTED
    tp.sortie.status = SortieStatus.TRAINING_SUBMITTED

    create_audit_log(db, actor, "TRAINING_SUBMITTED", "training_progress", tp.id,
                     old_value=old, new_value="SUBMITTED")
    db.commit()
    db.refresh(tp)
    return tp


def approve_training(db: Session, tp_id: int, actor: User) -> TrainingProgress:
    assert_can_approve_training(actor)
    tp = get_tp_or_404(db, tp_id)

    if tp.status != TrainingStatus.SUBMITTED:
        raise ConflictError(f"Can only approve SUBMITTED training. Current: {tp.status.value}")

    old = tp.status.value
    tp.status = TrainingStatus.APPROVED
    tp.approved_by = actor.id
    tp.approved_at = datetime.now(timezone.utc)
    tp.sortie.status = SortieStatus.TRAINING_APPROVED

    create_audit_log(db, actor, "TRAINING_APPROVED", "training_progress", tp.id,
                     old_value=old, new_value="APPROVED")
    db.commit()
    db.refresh(tp)
    return tp


def reject_training(db: Session, tp_id: int, data: TrainingReject, actor: User) -> TrainingProgress:
    assert_can_approve_training(actor)
    tp = get_tp_or_404(db, tp_id)

    if tp.status != TrainingStatus.SUBMITTED:
        raise ConflictError(f"Can only reject SUBMITTED training. Current: {tp.status.value}")

    if not data.rejection_reason or not data.rejection_reason.strip():
        raise ValidationError("Rejection reason is required", "rejection_reason")

    old = tp.status.value
    tp.status = TrainingStatus.REJECTED
    tp.rejection_reason = data.rejection_reason
    # Revert sortie to LANDED so instructor can resubmit
    tp.sortie.status = SortieStatus.LANDED

    create_audit_log(db, actor, "TRAINING_REJECTED", "training_progress", tp.id,
                     old_value=old, new_value="REJECTED", reason=data.rejection_reason)
    db.commit()
    db.refresh(tp)
    return tp