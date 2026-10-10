"""Standalone development data seeder.

This module seeds the database with realistic Sri Lanka dummy data on FastAPI
startup. It is intentionally kept OUT of the Alembic migrations so that in
production you can simply delete this file to disable all seeding (the startup
hook in ``__init__.py`` catches ``ImportError``).

Behaviour:
- Idempotent: if the primary admin account already exists, seeding is skipped
  so repeated restarts never crash on unique constraints.
- Every actor (admin, ministry, zonal officer, teacher, student) is linked to a
  ``user_account`` with password ``root`` (see ``DEFAULT_PASSWORD``) and is
  marked approved, so you can sign in immediately.

Run automatically via FastAPI startup, or manually with::

    python seed.py
"""

import random
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.core.database import Session
from src.core.passwords import hash_password
from src.models import (
    Admin,
    EducationalZone,
    ElectricityRecord,
    MinistryOfficer,
    MonthlyRecord,
    MonthlyRecordMark,
    Province,
    ReportSnapshot,
    Role,
    Student,
    Subject,
    Teacher,
    UserAccount,
    ZonalOfficer,
    student_teacher,
)
from src.repositories.account_repo import normalize_email

DEFAULT_PASSWORD = "root"
ADMIN_EMAIL = "hamdhiharis@gmail.com"

# Deterministic UUIDs so re-running is stable.
_SEED_NS = uuid.NAMESPACE_URL


def _sid(kind: str, name: str) -> uuid.UUID:
    return uuid.uuid5(_SEED_NS, f"csl01:seed:{kind}:{name}")


# ---------------------------------------------------------------------------
# Static Sri Lanka reference data
# ---------------------------------------------------------------------------

# province -> educational zones (real Sri Lanka zones)
PROVINCE_ZONES = {
    "Western Province": ["Colombo", "Gampaha", "Kalutara"],
    "Central Province": ["Kandy", "Matale", "Nuwara Eliya"],
    "Southern Province": ["Galle", "Matara", "Hambantota"],
    "Northern Province": ["Jaffna", "Kilinochchi", "Vavuniya"],
    "Eastern Province": ["Batticaloa", "Ampara", "Trincomalee"],
    "North Western Province": ["Kurunegala", "Puttalam"],
    "North Central Province": ["Anuradhapura", "Polonnaruwa"],
    "Uva Province": ["Badulla", "Monaragala"],
    "Sabaragamuwa Province": ["Kegalle", "Ratnapura"],
}

FIRST_NAMES = [
    "Nimal", "Sunil", "Kamal", "Ruwan", "Dinesh", "Asela", "Thilina",
    "Chamara", "Lahiru", "Sahan", "Fazal", "Ravi", "Kumar", "Anushka",
    "Pasindu", "Malith", "Charith", "Dilshan", "Ishara", "Kavindu",
    "Nimali", "Anoma", "Tharindi", "Sewwandi", "Dilani", "Harsha",
    "Sandun", "Pradeep", "Mahesh", "Janith",
]
LAST_NAMES = [
    "Perera", "Fernando", "Silva", "Jayasinghe", "Kumara", "Bandara",
    "Rajapaksa", "Wijesinghe", "Dissanayake", "Gunasekara", "Mohamed",
    "Nathan", "Gamage", "Herath", "Jayawardena", "Senanayake",
    "Weerasinghe", "Madushan", "Nirmal",
]
SCHOOLS = [
    "Royal College", "D.S. Senanayake College", "Ananda College",
    "Nalanda College", "Mahinda College", "Richmond College",
    "St. Peter's College", "Trinity College", "Dharmaraja College",
    "Kingswood College", "Wesley College", "Musaeus College",
    "Maliyadeva College", "Bandaranayake College", "Rahula College",
    "Seethawaka College", "Hillwood College", "St. Joseph's College",
]

# grade -> (stream -> subject names)
GENERAL_SUBJECTS = [
    "Mathematics", "Science", "English", "Sinhala", "Tamil",
    "History", "Geography",
]
STREAM_SUBJECTS = {
    "Physical Science": [
        "Combined Mathematics", "Physics", "Chemistry", "Biology",
    ],
    "Commerce": ["Accounting", "Business Studies", "Economics"],
    "Arts": ["Political Science", "Logic", "Media Studies"],
    "Technology": ["Engineering Technology", "Science for Technology"],
}


def _person(index: int) -> str:
    rng = random.Random(1000 + index)
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _role_id(db, name: str) -> uuid.UUID:
    role = db.scalar(select(Role).where(Role.name == name))
    if role is None:
        raise RuntimeError(
            f"Role {name!r} is missing. Run `alembic upgrade head` first."
        )
    return role.role_id


def _add_account(db, actor_type: str, actor_id: uuid.UUID, email: str) -> None:
    """Create a user_account for an actor if one does not already exist."""
    normalized = normalize_email(email)
    exists = db.scalar(
        select(UserAccount.account_id).where(
            UserAccount.email == normalized
        )
    )
    if exists is not None:
        return
    db.add(
        UserAccount(
            account_id=uuid.uuid4(),
            email=normalized,
            actor_type=actor_type,
            actor_id=actor_id,
            password_hash=hash_password(DEFAULT_PASSWORD),
            created_at=datetime.now(UTC),
        )
    )


def _email_from_name(name: str, domain: str = "csl.lk") -> str:
    slug = "".join(ch for ch in name.lower() if ch.isalnum())
    return f"{slug}@{domain}"


def _provinces_and_zones(db) -> list[tuple[Province, list[EducationalZone]]]:
    """Ensure all 9 Sri Lanka provinces and their zones exist; return them.

    Provinces/zones may already exist (seeded by migrations with their own
    UUIDs), so look them up by name before inserting to stay idempotent.
    """
    result: list[tuple[Province, list[EducationalZone]]] = []
    for prov_name, zone_names in PROVINCE_ZONES.items():
        province = db.scalar(
            select(Province).where(Province.Province_name == prov_name)
        )
        if province is None:
            province = Province(
                prov_id=_sid("province", prov_name), Province_name=prov_name
            )
            db.add(province)
            db.flush()
        zones: list[EducationalZone] = []
        for zone_name in zone_names:
            zone = db.scalar(
                select(EducationalZone).where(
                    EducationalZone.name == zone_name,
                    EducationalZone.prov_id == province.prov_id,
                )
            )
            if zone is None:
                zone = EducationalZone(
                    zone_id=_sid("zone", f"{prov_name}:{zone_name}"),
                    name=zone_name,
                    prov_id=province.prov_id,
                )
                db.add(zone)
                db.flush()
            zones.append(zone)
        result.append((province, zones))
    return result


def _seed_subjects(db) -> dict[str, dict[str, list[Subject]]]:
    """Create general + stream subjects. Returns {grade: {stream: [subjects]}}."""
    catalog: dict[str, dict[str, list[Subject]]] = {}
    for grade in [str(g) for g in range(1, 14)]:
        catalog.setdefault(grade, {})
        streams = [""]
        if grade in {"12", "13"}:
            streams = list(STREAM_SUBJECTS.keys())
        for stream in streams:
            names = (
                list(STREAM_SUBJECTS[stream])
                if grade in {"12", "13"} and stream
                else GENERAL_SUBJECTS
            )
            subjects: list[Subject] = []
            for name in names:
                name_key = " ".join(name.split()).casefold()
                existing = db.scalar(
                    select(Subject).where(
                        Subject.grade == grade,
                        Subject.stream == stream,
                        Subject.name_key == name_key,
                    )
                )
                if existing is None:
                    existing = Subject(
                        subject_id=uuid.uuid4(),
                        name=name,
                        name_key=name_key,
                        grade=grade,
                        stream=stream,
                        active=True,
                    )
                    db.add(existing)
                    db.flush()
                subjects.append(existing)
            catalog[grade][stream] = subjects
    return catalog


# ---------------------------------------------------------------------------
# Actor seeders
# ---------------------------------------------------------------------------


def _seed_admin(db) -> Admin:
    """Create the primary admin (hamdhiharis@gmail.com / root) plus dummies."""
    admin_role = _role_id(db, "ADMIN")
    primary_id = _sid("admin", ADMIN_EMAIL)
    primary = db.scalar(
        select(Admin).where(Admin.admin_email == ADMIN_EMAIL)
    )
    if primary is None:
        primary = Admin(
            admin_id=primary_id,
            admin_name="Hamdhi Haris",
            admin_email=ADMIN_EMAIL,
            role_id=admin_role,
        )
        db.add(primary)
        db.flush()
    _add_account(db, "admin", primary.admin_id, ADMIN_EMAIL)

    # A few extra dummy admins for variety.
    for i in range(4):
        name = f"Admin {_person(i)}"
        email = _email_from_name(f"admin{i}", "csl.lk")
        admin = db.scalar(select(Admin).where(Admin.admin_email == email))
        if admin is None:
            admin = Admin(
                admin_id=_sid("admin", email),
                admin_name=name[:36],
                admin_email=email,
                role_id=admin_role,
            )
            db.add(admin)
            db.flush()
        _add_account(db, "admin", admin.admin_id, email)
    return primary


def _seed_ministry(db, admin: Admin) -> MinistryOfficer:
    """Create exactly ONE ministry officer."""
    ministry_role = _role_id(db, "MINISTRY")
    email = "ministry@csl.lk"
    mini_id = _sid("ministry", email)
    officer = db.get(MinistryOfficer, mini_id)
    if officer is None:
        officer = MinistryOfficer(
            mini_id=mini_id,
            name="Ministry Officer",
            email=email,
            approval_status="approved",
            admin_id=admin.admin_id,
            role_id=ministry_role,
        )
        db.add(officer)
        db.flush()
    _add_account(db, "ministry", officer.mini_id, email)
    return officer


def _seed_zonal_officers(db, ministry, prov_zones) -> list[ZonalOfficer]:
    zonal_role = _role_id(db, "ZONAL")
    officers: list[ZonalOfficer] = []
    idx = 0
    for _province, zones in prov_zones:
        for zone in zones:
            idx += 1
            name = f"Zonal Officer {_person(idx)}"
            email = _email_from_name(f"zonal{idx}", "csl.lk")
            zonal_id = _sid("zonal", email)
            officer = db.get(ZonalOfficer, zonal_id)
            if officer is None:
                officer = ZonalOfficer(
                    zonal_id=zonal_id,
                    name=name,
                    approval_status="approved",
                    mini_id=ministry.mini_id,
                    zone_id=zone.zone_id,
                    role_id=zonal_role,
                )
                db.add(officer)
                db.flush()
            _add_account(db, "zonal", officer.zonal_id, email)
            officers.append(officer)
    return officers


def _seed_teachers(db, prov_zones, catalog) -> list[Teacher]:
    teacher_role = _role_id(db, "TEACHER")
    teachers: list[Teacher] = []
    # Flatten zones with their provinces for spreading teachers around.
    zone_list = [zone for _p, zones in prov_zones for zone in zones]
    idx = 0
    for zone in zone_list:
        for _ in range(2):  # a couple of teachers per zone
            idx += 1
            name = _person(100 + idx)
            email = _email_from_name(f"teacher{idx}", "csl.lk")
            tid = _sid("teacher", email)
            teacher = db.get(Teacher, tid)
            if teacher is None:
                # Pick a subject for a mid/high grade so it is broadly usable.
                grade = "11"
                subject = catalog[grade][""][0]
                teacher = Teacher(
                    tid=tid,
                    teacher_code=f"T{idx:04d}",
                    Name=name,
                    Subject=subject.name,
                    approval_status="approved",
                    subject_id=subject.subject_id,
                    School=SCHOOLS[idx % len(SCHOOLS)],
                    zonal_id=zone.zone_id,
                    role_id=teacher_role,
                )
                db.add(teacher)
                db.flush()
            _add_account(db, "teacher", teacher.tid, email)
            teachers.append(teacher)
    return teachers


def _seed_electricity(db) -> list[ElectricityRecord]:
    records: list[ElectricityRecord] = []
    for i, school in enumerate(SCHOOLS):
        acc = f"ACC{i:04d}"
        rec = db.get(ElectricityRecord, acc)
        if rec is None:
            rec = ElectricityRecord(acc_number=acc, acc_name=f"{school} - Main")
            db.add(rec)
            db.flush()
        records.append(rec)
    return records


def _seed_students(db, prov_zones, teachers, catalog, electricity) -> list[Student]:
    """Create 20 students spread across provinces, zones and teachers."""
    student_role = _role_id(db, "STUDENT")
    # All seeded teachers use grade 11 / no stream, so match students to that.
    grade = "11"
    stream = ""
    students: list[Student] = []
    zone_list = [zone for _p, zones in prov_zones for zone in zones]
    for i in range(20):
        idx = i + 1
        name = _person(500 + idx)
        email = _email_from_name(f"student{idx}", "csl.lk")
        stid = _sid("student", email)
        student = db.get(Student, stid)
        if student is None:
            zone = zone_list[i % len(zone_list)]
            teacher = teachers[i % len(teachers)]
            student = Student(
                stid=stid,
                Name=name,
                Grade=grade,
                stream=stream,
                School=SCHOOLS[i % len(SCHOOLS)],
                Gmail=email,
                registration_status="approved",
                zone_id=zone.zone_id,
                acc_number=electricity[i % len(electricity)].acc_number,
                role_id=student_role,
            )
            db.add(student)
            db.flush()
            # Link student <-> teacher via the association table (approved).
            db.add(
                student_teacher(
                    stid=student.stid,
                    tid=teacher.tid,
                    assignment_status="approved",
                )
            )
        _add_account(db, "student", student.stid, email)
        students.append(student)
    return students


def _seed_monthly_records(db, students, catalog) -> None:
    """Create approved monthly records with subject marks for each student."""
    grade = "11"
    stream = ""
    subjects = catalog[grade][stream]
    today = datetime.now(UTC).date()
    months = [
        date(today.year, today.month, 1) - timedelta(days=30 * k)
        for k in range(3)
    ]
    rng = random.Random(42)
    for student in students:
        for month in months:
            existing = db.scalar(
                select(MonthlyRecord).where(
                    MonthlyRecord.fk_stid == student.stid,
                    MonthlyRecord.reporting_month == month,
                )
            )
            if existing is not None:
                continue
            record = MonthlyRecord(
                id=uuid.uuid4(),
                fk_stid=student.stid,
                fk_tid=None,
                reporting_month=month,
                upload_date=datetime.now(UTC),
                approved=True,
            )
            db.add(record)
            db.flush()
            for subject in subjects:
                max_score = Decimal(100)
                score = Decimal(rng.randint(45, 100))
                db.add(
                    MonthlyRecordMark(
                        mark_id=uuid.uuid4(),
                        monthly_record_id=record.id,
                        subject_id=subject.subject_id,
                        score=score,
                        max_score=max_score,
                    )
                )


def _seed_report_snapshots(db, admin: Admin) -> None:
    """Create a couple of report snapshots so saved-report endpoints work."""
    if db.scalar(select(ReportSnapshot.report_id).limit(1)) is not None:
        return
    # generated_by_id is a FK to user_accounts.account_id.
    account_id = db.scalar(
        select(UserAccount.account_id).where(
            UserAccount.actor_type == "admin",
            UserAccount.actor_id == admin.admin_id,
        )
    )
    if account_id is None:
        return
    today = datetime.now(UTC).date()
    start = date(today.year, today.month, 1)
    db.add(
        ReportSnapshot(
            report_id=uuid.uuid4(),
            report_type="province",
            scope_type="province",
            scope_id=None,
            generated_by_id=account_id,
            start_date=start,
            end_date=today,
            generated_at=datetime.now(UTC),
            data=[{"note": "seed snapshot"}],
        )
    )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_seed() -> None:
    """Seed the database if it has not been seeded yet. Safe to call on every
    FastAPI startup: it is a no-op once the primary admin account exists."""
    db = Session()
    try:
        # Idempotency guard: if the primary admin account exists, skip.
        already = db.scalar(
            select(UserAccount.account_id).where(
                UserAccount.email == normalize_email(ADMIN_EMAIL)
            )
        )
        if already is not None:
            return

        prov_zones = _provinces_and_zones(db)
        catalog = _seed_subjects(db)
        admin = _seed_admin(db)
        ministry = _seed_ministry(db, admin)
        _seed_zonal_officers(db, ministry, prov_zones)
        teachers = _seed_teachers(db, prov_zones, catalog)
        electricity = _seed_electricity(db)
        students = _seed_students(db, prov_zones, teachers, catalog, electricity)
        _seed_monthly_records(db, students, catalog)
        _seed_report_snapshots(db, admin)

        db.commit()
        print(
            f"[seed] Database seeded: 9 provinces, "
            f"{len(students)} students, admin {ADMIN_EMAIL} (password: "
            f"{DEFAULT_PASSWORD})."
        )
    except IntegrityError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()



