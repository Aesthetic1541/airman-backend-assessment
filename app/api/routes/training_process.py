from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.schemas.training_progress import (
    TrainingCreate, TrainingSubmit, TrainingReject, TrainingResponse
)
from app.core.security import get_current_user
from app.core.permissions import require_instructor_or_above, require_cfi_or_admin
from app.services import training_service

router = APIRouter(prefix="/training-progress", tags=["Training Progress"])


@router.post("", response_model=TrainingResponse, status_code=201)
def create(
    data: TrainingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor_or_above)
):
    return training_service.create_training(db, data, current_user)


@router.get("/{sortie_id}", response_model=TrainingResponse)
def get_by_sortie(
    sortie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return training_service.get_training_by_sortie(db, sortie_id, current_user)


@router.patch("/{tp_id}/submit", response_model=TrainingResponse)
def submit(
    tp_id: int,
    data: TrainingSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor_or_above)
):
    return training_service.submit_training(db, tp_id, data, current_user)


@router.patch("/{tp_id}/approve", response_model=TrainingResponse)
def approve(
    tp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_cfi_or_admin)
):
    return training_service.approve_training(db, tp_id, current_user)


@router.patch("/{tp_id}/reject", response_model=TrainingResponse)
def reject(
    tp_id: int,
    data: TrainingReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_cfi_or_admin)
):
    return training_service.reject_training(db, tp_id, data, current_user)