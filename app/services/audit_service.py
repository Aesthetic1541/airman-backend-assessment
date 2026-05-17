from sqlalchemy.orm import Session
from app.db.models import AuditLog, User


def create_audit_log(
    db: Session,
    actor: User,
    action: str,
    entity_type: str,
    entity_id: int,
    old_value: str = None,
    new_value: str = None,
    reason: str = None,
) -> AuditLog:
    """
    Creates an immutable audit log entry.
    Called after every critical state change in the system.
    """
    log = AuditLog(
        actor_id=actor.id,
        actor_role=actor.role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
    )
    db.add(log)
    # We do NOT commit here — the calling service owns the transaction.
    return log