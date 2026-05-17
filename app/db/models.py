"""
SQLAlchemy ORM models for the Skynet Flight Operations API.
Every table has created_at / updated_at timestamps and relevant indexes.
"""
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    Enum as SAEnum, Float, Boolean, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.db.database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    DISPATCHER = "DISPATCHER"
    INSTRUCTOR = "INSTRUCTOR"
    CFI = "CFI"
    CADET = "CADET"
    MAINTENANCE_OFFICER = "MAINTENANCE_OFFICER"


class AircraftStatus(str, enum.Enum):
    READY = "READY"
    SCHEDULED = "SCHEDULED"
    AIRBORNE = "AIRBORNE"
    LANDED = "LANDED"
    GROUNDED = "GROUNDED"
    MAINTENANCE = "MAINTENANCE"


class SortieStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    RELEASED = "RELEASED"
    AIRBORNE = "AIRBORNE"
    LANDED = "LANDED"
    TRAINING_SUBMITTED = "TRAINING_SUBMITTED"
    TRAINING_APPROVED = "TRAINING_APPROVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    AIRCRAFT_GROUNDED = "AIRCRAFT_GROUNDED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


class TrainingStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DefectStatus(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    DEFERRED = "DEFERRED"


class DefectSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ---------------------------------------------------------------------------
# Timestamp mixin
# ---------------------------------------------------------------------------

def utcnow():
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

class Base_(TimestampMixin, Base):
    """A physical flight-school base / location."""
    __tablename__ = "bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    location = Column(String(200), nullable=False)

    users = relationship("User", back_populates="base")
    aircraft = relationship("Aircraft", back_populates="base")
    sorties = relationship("Sortie", back_populates="base")


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, index=True)
    base_id = Column(Integer, ForeignKey("bases.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    base = relationship("Base_", back_populates="users")
    cadet_sorties = relationship("Sortie", foreign_keys="Sortie.cadet_id", back_populates="cadet")
    instructor_sorties = relationship("Sortie", foreign_keys="Sortie.instructor_id", back_populates="instructor")
    training_records = relationship("TrainingProgress", foreign_keys="TrainingProgress.instructor_id", back_populates="instructor")
    reported_defects = relationship("Defect", foreign_keys="Defect.reported_by", back_populates="reporter")
    resolved_defects = relationship("Defect", foreign_keys="Defect.resolved_by", back_populates="resolver")
    audit_logs = relationship("AuditLog", back_populates="actor")


class Aircraft(TimestampMixin, Base):
    __tablename__ = "aircraft"

    id = Column(Integer, primary_key=True, index=True)
    registration = Column(String(20), unique=True, nullable=False, index=True)
    aircraft_type = Column(String(100), nullable=False)
    base_id = Column(Integer, ForeignKey("bases.id"), nullable=False, index=True)
    status = Column(SAEnum(AircraftStatus), nullable=False, default=AircraftStatus.READY, index=True)
    tbo_remaining_hours = Column(Float, nullable=True)

    base = relationship("Base_", back_populates="aircraft")
    sorties = relationship("Sortie", back_populates="aircraft")
    defects = relationship("Defect", back_populates="aircraft")


class Sortie(TimestampMixin, Base):
    __tablename__ = "sorties"

    id = Column(Integer, primary_key=True, index=True)
    sortie_number = Column(String(20), unique=True, nullable=False, index=True)
    cadet_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"), nullable=False, index=True)
    base_id = Column(Integer, ForeignKey("bases.id"), nullable=False, index=True)
    lesson_type = Column(String(100), nullable=False)
    scheduled_start = Column(DateTime(timezone=True), nullable=False)
    scheduled_end = Column(DateTime(timezone=True), nullable=False)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)
    status = Column(SAEnum(SortieStatus), nullable=False, default=SortieStatus.SCHEDULED, index=True)
    delay_minutes = Column(Integer, default=0)
    cancel_reason = Column(Text, nullable=True)

    cadet = relationship("User", foreign_keys=[cadet_id], back_populates="cadet_sorties")
    instructor = relationship("User", foreign_keys=[instructor_id], back_populates="instructor_sorties")
    aircraft = relationship("Aircraft", back_populates="sorties")
    base = relationship("Base_", back_populates="sorties")
    training_progress = relationship("TrainingProgress", back_populates="sortie", uselist=False)
    defects = relationship("Defect", back_populates="sortie")

    __table_args__ = (
        Index("ix_sorties_aircraft_schedule", "aircraft_id", "scheduled_start", "scheduled_end"),
    )


class TrainingProgress(TimestampMixin, Base):
    __tablename__ = "training_progress"

    id = Column(Integer, primary_key=True, index=True)
    sortie_id = Column(Integer, ForeignKey("sorties.id"), unique=True, nullable=False, index=True)
    cadet_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    lesson_type = Column(String(100), nullable=False)
    maneuver_score = Column(Integer, nullable=True)
    communication_score = Column(Integer, nullable=True)
    situational_awareness_score = Column(Integer, nullable=True)
    remarks = Column(Text, nullable=True)
    status = Column(SAEnum(TrainingStatus), nullable=False, default=TrainingStatus.DRAFT, index=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    sortie = relationship("Sortie", back_populates="training_progress")
    cadet = relationship("User", foreign_keys=[cadet_id])
    instructor = relationship("User", foreign_keys=[instructor_id], back_populates="training_records")
    approver = relationship("User", foreign_keys=[approved_by])


class Defect(TimestampMixin, Base):
    __tablename__ = "defects"

    id = Column(Integer, primary_key=True, index=True)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"), nullable=False, index=True)
    sortie_id = Column(Integer, ForeignKey("sorties.id"), nullable=True, index=True)
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    severity = Column(SAEnum(DefectSeverity), nullable=False, index=True)
    description = Column(Text, nullable=False)
    status = Column(SAEnum(DefectStatus), nullable=False, default=DefectStatus.OPEN, index=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    aircraft = relationship("Aircraft", back_populates="defects")
    sortie = relationship("Sortie", back_populates="defects")
    reporter = relationship("User", foreign_keys=[reported_by], back_populates="reported_defects")
    resolver = relationship("User", foreign_keys=[resolved_by], back_populates="resolved_defects")


class AuditLog(Base):
    """Immutable audit trail — no updated_at, never deleted."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    actor_role = Column(SAEnum(UserRole), nullable=False)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    actor = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id"),
    )