"""
RBAC permission definitions and reusable FastAPI dependencies.
All authorization checks are enforced here — never just on the frontend.
"""
from functools import wraps
from fastapi import Depends
from app.core.errors import ForbiddenError
from app.core.security import get_current_user
from app.db.models import User, UserRole


# ---------------------------------------------------------------------------
# Role-based dependency factories
# ---------------------------------------------------------------------------

def require_roles(*roles: UserRole):
    """Return a FastAPI dependency that checks the current user's role."""
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenError()
        return current_user
    return dependency


# Pre-built dependencies for common role sets
require_admin = require_roles(UserRole.ADMIN)

require_dispatcher_or_admin = require_roles(UserRole.ADMIN, UserRole.DISPATCHER)

require_maintenance_or_admin = require_roles(UserRole.ADMIN, UserRole.MAINTENANCE_OFFICER)

require_cfi_or_admin = require_roles(UserRole.ADMIN, UserRole.CFI)

require_instructor_or_above = require_roles(
    UserRole.ADMIN, UserRole.DISPATCHER, UserRole.INSTRUCTOR, UserRole.CFI
)

require_any_authenticated = require_roles(
    UserRole.ADMIN, UserRole.DISPATCHER, UserRole.INSTRUCTOR,
    UserRole.CFI, UserRole.CADET, UserRole.MAINTENANCE_OFFICER
)


# ---------------------------------------------------------------------------
# Base-scope enforcement helpers (used in service layer)
# ---------------------------------------------------------------------------

def assert_same_base(user: User, entity_base_id: int, allow_admin: bool = True):
    """Raise ForbiddenError if user doesn't belong to the entity's base."""
    if allow_admin and user.role == UserRole.ADMIN:
        return
    if user.base_id != entity_base_id:
        raise ForbiddenError("Access denied: base scope mismatch")


def assert_can_manage_sortie_workflow(user: User):
    """Only DISPATCHER or ADMIN may drive sortie state transitions."""
    if user.role not in (UserRole.ADMIN, UserRole.DISPATCHER):
        raise ForbiddenError("Only dispatchers can manage sortie workflow")


def assert_can_submit_training(user: User, sortie_instructor_id: int):
    """Only the assigned instructor (or admin) may submit training progress."""
    if user.role == UserRole.ADMIN:
        return
    if user.role != UserRole.INSTRUCTOR:
        raise ForbiddenError("Only instructors can submit training progress")
    if user.id != sortie_instructor_id:
        raise ForbiddenError("You can only submit training for sorties assigned to you")


def assert_can_approve_training(user: User):
    if user.role not in (UserRole.ADMIN, UserRole.CFI):
        raise ForbiddenError("Only CFI can approve or reject training progress")


def assert_can_manage_defects(user: User):
    if user.role not in (UserRole.ADMIN, UserRole.MAINTENANCE_OFFICER):
        raise ForbiddenError("Only maintenance officers can resolve or defer defects")


def assert_can_view_sortie(user: User, sortie):
    """Cadets can only view their own sorties; instructors see assigned ones."""
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.CADET and sortie.cadet_id != user.id:
        raise ForbiddenError("Cadets can only view their own sorties")
    if user.role == UserRole.INSTRUCTOR and sortie.instructor_id != user.id:
        raise ForbiddenError("Instructors can only view their assigned sorties")
    # Dispatcher / CFI / Maintenance see all within base
    assert_same_base(user, sortie.base_id)