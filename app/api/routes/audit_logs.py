from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.db.database import get_db
from app.db.models import User, AuditLog, UserRole
from app.schemas.audit_log import AuditLogResponse
from app.schemas.base import PaginatedResponse
from app.core.security import get_current_user
from app.core.errors import ForbiddenError

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
def list_audit_logs(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only admin, CFI, and dispatcher can see audit logs
    allowed = (UserRole.ADMIN, UserRole.CFI, UserRole.DISPATCHER)
    if current_user.role not in allowed:
        raise ForbiddenError("Access to audit logs requires ADMIN, CFI, or DISPATCHER role")

    q = db.query(AuditLog)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.filter(AuditLog.entity_id == entity_id)
    q = q.order_by(AuditLog.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=items, total=total, page=page,
        page_size=page_size, pages=math.ceil(total / page_size) or 1
    )