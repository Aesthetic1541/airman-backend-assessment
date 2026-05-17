"""
Permission service — thin wrapper that re-exports core permission helpers.
Keeps services from importing directly from app.core.permissions,
giving us one place to extend or audit permission checks.
"""
from app.core.permissions import (
    assert_same_base,
    assert_can_manage_sortie_workflow,
    assert_can_submit_training,
    assert_can_approve_training,
    assert_can_manage_defects,
    assert_can_view_sortie,
)

__all__ = [
    "assert_same_base",
    "assert_can_manage_sortie_workflow",
    "assert_can_submit_training",
    "assert_can_approve_training",
    "assert_can_manage_defects",
    "assert_can_view_sortie",
]