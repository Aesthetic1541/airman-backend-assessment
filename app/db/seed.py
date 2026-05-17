"""
Seed script for development and testing.
Run: python -m app.db.seed
Creates 2 bases, 3 aircraft, 6 users, 5 sorties, 2 training records, 2 defects.
"""
import sys
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, engine
from app.db.models import Base, Base_, User, Aircraft, Sortie, TrainingProgress, Defect
from app.db.models import UserRole, AircraftStatus, SortieStatus, TrainingStatus, DefectStatus, DefectSeverity
from app.core.security import hash_password


def utcnow():
    return datetime.now(timezone.utc)


def seed(db: Session):
    # -----------------------------------------------------------------------
    # Bases
    # -----------------------------------------------------------------------
    base_delhi = Base_(name="Delhi Flying Club", code="DFC", location="Safdarjung Airport, New Delhi")
    base_mumbai = Base_(name="Mumbai Aero Academy", code="MAA", location="Juhu Airport, Mumbai")
    db.add_all([base_delhi, base_mumbai])
    db.flush()

    # -----------------------------------------------------------------------
    # Users
    # -----------------------------------------------------------------------
    admin = User(
        full_name="Admin User", email="admin@skynet.aero",
        hashed_password=hash_password("Admin@1234"),
        role=UserRole.ADMIN, base_id=base_delhi.id
    )
    dispatcher = User(
        full_name="Dispatch Officer", email="dispatch@skynet.aero",
        hashed_password=hash_password("Dispatch@1234"),
        role=UserRole.DISPATCHER, base_id=base_delhi.id
    )
    instructor = User(
        full_name="Capt. Rao", email="capt.rao@skynet.aero",
        hashed_password=hash_password("Instructor@1234"),
        role=UserRole.INSTRUCTOR, base_id=base_delhi.id
    )
    cfi = User(
        full_name="Chief Flying Instructor", email="cfi@skynet.aero",
        hashed_password=hash_password("CFI@12345"),
        role=UserRole.CFI, base_id=base_delhi.id
    )
    cadet = User(
        full_name="Arjun Menon", email="arjun@skynet.aero",
        hashed_password=hash_password("Cadet@1234"),
        role=UserRole.CADET, base_id=base_delhi.id
    )
    maintenance = User(
        full_name="Maintenance Officer", email="maint@skynet.aero",
        hashed_password=hash_password("Maint@1234"),
        role=UserRole.MAINTENANCE_OFFICER, base_id=base_delhi.id
    )
    db.add_all([admin, dispatcher, instructor, cfi, cadet, maintenance])
    db.flush()

    # -----------------------------------------------------------------------
    # Aircraft
    # -----------------------------------------------------------------------
    ac_abc = Aircraft(
        registration="VT-ABC", aircraft_type="Cessna 172",
        base_id=base_delhi.id, status=AircraftStatus.READY, tbo_remaining_hours=450.0
    )
    ac_sky = Aircraft(
        registration="VT-SKY", aircraft_type="Piper PA-28",
        base_id=base_delhi.id, status=AircraftStatus.GROUNDED, tbo_remaining_hours=220.0
    )
    ac_air = Aircraft(
        registration="VT-AIR", aircraft_type="Diamond DA40",
        base_id=base_delhi.id, status=AircraftStatus.READY, tbo_remaining_hours=380.0
    )
    db.add_all([ac_abc, ac_sky, ac_air])
    db.flush()

    now = utcnow()

    # -----------------------------------------------------------------------
    # Sorties
    # -----------------------------------------------------------------------
    s001 = Sortie(
        sortie_number="S001", cadet_id=cadet.id, instructor_id=instructor.id,
        aircraft_id=ac_abc.id, base_id=base_delhi.id, lesson_type="Navigation",
        scheduled_start=now + timedelta(hours=2), scheduled_end=now + timedelta(hours=4),
        status=SortieStatus.SCHEDULED
    )
    s002 = Sortie(
        sortie_number="S002", cadet_id=cadet.id, instructor_id=instructor.id,
        aircraft_id=ac_air.id, base_id=base_delhi.id, lesson_type="Circuits",
        scheduled_start=now - timedelta(hours=1), scheduled_end=now + timedelta(hours=1),
        status=SortieStatus.RELEASED
    )
    s003 = Sortie(
        sortie_number="S003", cadet_id=cadet.id, instructor_id=instructor.id,
        aircraft_id=ac_abc.id, base_id=base_delhi.id, lesson_type="Solo",
        scheduled_start=now - timedelta(hours=3), scheduled_end=now - timedelta(hours=1),
        actual_start=now - timedelta(hours=3), status=SortieStatus.AIRBORNE
    )
    s004 = Sortie(
        sortie_number="S004", cadet_id=cadet.id, instructor_id=instructor.id,
        aircraft_id=ac_air.id, base_id=base_delhi.id, lesson_type="Instrument",
        scheduled_start=now - timedelta(hours=6), scheduled_end=now - timedelta(hours=4),
        actual_start=now - timedelta(hours=6), actual_end=now - timedelta(hours=4),
        status=SortieStatus.LANDED
    )
    s005 = Sortie(
        sortie_number="S005", cadet_id=cadet.id, instructor_id=instructor.id,
        aircraft_id=ac_abc.id, base_id=base_delhi.id, lesson_type="Night Flying",
        scheduled_start=now - timedelta(hours=10), scheduled_end=now - timedelta(hours=8),
        actual_start=now - timedelta(hours=10), actual_end=now - timedelta(hours=8),
        status=SortieStatus.TRAINING_SUBMITTED
    )
    db.add_all([s001, s002, s003, s004, s005])
    db.flush()

    # -----------------------------------------------------------------------
    # Training progress
    # -----------------------------------------------------------------------
    tp1 = TrainingProgress(
        sortie_id=s005.id, cadet_id=cadet.id, instructor_id=instructor.id,
        lesson_type="Night Flying", maneuver_score=4, communication_score=3,
        situational_awareness_score=4, remarks="Good situational awareness. Work on radio calls.",
        status=TrainingStatus.SUBMITTED, submitted_at=utcnow()
    )
    tp2 = TrainingProgress(
        sortie_id=s004.id, cadet_id=cadet.id, instructor_id=instructor.id,
        lesson_type="Instrument", maneuver_score=5, communication_score=4,
        situational_awareness_score=5, remarks="Excellent instrument scan. Ready for next level.",
        status=TrainingStatus.DRAFT
    )
    db.add_all([tp1, tp2])
    db.flush()

    # -----------------------------------------------------------------------
    # Defects
    # -----------------------------------------------------------------------
    d1 = Defect(
        aircraft_id=ac_sky.id, sortie_id=None, reported_by=maintenance.id,
        severity=DefectSeverity.CRITICAL,
        description="Hydraulic fluid leak detected in left landing gear actuator",
        status=DefectStatus.OPEN
    )
    d2 = Defect(
        aircraft_id=ac_abc.id, sortie_id=s004.id, reported_by=instructor.id,
        severity=DefectSeverity.LOW,
        description="Minor scratch on fuselage near door handle — cosmetic only",
        status=DefectStatus.DEFERRED
    )
    db.add_all([d1, d2])
    db.commit()
    print("✅ Seed data created successfully.")
    print(f"   Bases: {base_delhi.code}, {base_mumbai.code}")
    print(f"   Users: admin, dispatch, instructor, cfi, cadet, maintenance")
    print(f"   Aircraft: VT-ABC, VT-SKY, VT-AIR")
    print(f"   Sorties: S001–S005")
    print(f"   Login: admin@skynet.aero / Admin@1234")


def main():
    from app.db.models import Base as OrmBase
    OrmBase.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Idempotent: skip if already seeded
        if db.query(User).count() > 0:
            print("ℹ️  Database already seeded. Skipping.")
            return
        seed(db)
    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()