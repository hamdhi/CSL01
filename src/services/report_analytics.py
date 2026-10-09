"""Aggregated performance analytics used to build JSON and PDF reports.

These helpers query monthly marks for a period and aggregate them into table
rows (with accompanying chart series) for each reporting scope. Averages use
approved records only, matching the existing convention in ``report_repo``.
"""

import uuid
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.educational_zone import EducationalZone
from src.models.monthly_record import MonthlyRecord
from src.models.monthly_record_mark import MonthlyRecordMark
from src.models.province import Province
from src.models.student import Student
from src.models.student_teacher import student_teacher
from src.models.subject import Subject
from src.models.teacher import Teacher


def _pct(score: Decimal, max_score: Decimal) -> Decimal:
    return (Decimal(score) / Decimal(max_score) * Decimal(100)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def _avg(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0.00")
    return (sum(values) / Decimal(len(values))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def fetch_marks(
    db: Session,
    start_date: date,
    end_date: date,
    *,
    zone_id: uuid.UUID | None = None,
    province_id: uuid.UUID | None = None,
    student_id: uuid.UUID | None = None,
    teacher_id: uuid.UUID | None = None,
    approved_only: bool = True,
) -> list[dict[str, Any]]:
    """Return one row per subject mark within the period for the given scope."""
    statement = (
        select(
            MonthlyRecordMark,
            MonthlyRecord,
            Student,
            EducationalZone,
            Province,
            Subject,
        )
        .join(MonthlyRecord, MonthlyRecord.id == MonthlyRecordMark.monthly_record_id)
        .join(Student, Student.stid == MonthlyRecord.fk_stid)
        .outerjoin(EducationalZone, EducationalZone.zone_id == Student.zone_id)
        .outerjoin(Province, Province.prov_id == EducationalZone.prov_id)
        .outerjoin(Subject, Subject.subject_id == MonthlyRecordMark.subject_id)
        .where(
            MonthlyRecord.reporting_month >= start_date,
            MonthlyRecord.reporting_month <= end_date,
        )
    )
    if approved_only:
        statement = statement.where(MonthlyRecord.approved.is_(True))
    if zone_id is not None:
        statement = statement.where(Student.zone_id == zone_id)
    if province_id is not None:
        statement = statement.where(EducationalZone.prov_id == province_id)
    if student_id is not None:
        statement = statement.where(Student.stid == student_id)
    if teacher_id is not None:
        statement = statement.where(MonthlyRecord.fk_tid == teacher_id)

    rows = db.execute(statement).all()
    results: list[dict[str, Any]] = []
    for mark, record, student, zone, province, subject in rows:
        results.append(
            {
                "student_id": student.stid,
                "student_name": student.Name,
                "grade": student.Grade,
                "stream": student.stream,
                "school": student.School,
                "zone_id": student.zone_id,
                "zone_name": zone.name if zone else None,
                "prov_id": province.prov_id if province else None,
                "province_name": province.Province_name if province else None,
                "subject_id": mark.subject_id,
                "subject": subject.name if subject else None,
                "score": mark.score,
                "max_score": mark.max_score,
                "percentage": _pct(mark.score, mark.max_score),
                "reporting_month": record.reporting_month,
                "fk_tid": record.fk_tid,
            }
        )
    return results


def _group_average(
    rows: list[dict[str, Any]], key: str
) -> list[dict[str, Any]]:
    grouped: dict[Any, list[Decimal]] = {}
    for row in rows:
        grouped.setdefault(row[key], []).append(row["percentage"])
    output: list[dict[str, Any]] = []
    for value, percentages in grouped.items():
        output.append({"key": value, "average_percentage": _avg(percentages)})
    return output


def monthly_trend(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[date, list[Decimal]] = {}
    for row in rows:
        grouped.setdefault(row["reporting_month"], []).append(row["percentage"])
    trend = [
        {"month": month, "average_percentage": _avg(percentages)}
        for month, percentages in grouped.items()
    ]
    trend.sort(key=lambda item: item["month"])
    return trend


def ministry_overview(
    db: Session, start_date: date, end_date: date
) -> dict[str, Any]:
    """Nationwide totals plus a per-province average breakdown."""
    rows = fetch_marks(db, start_date, end_date)
    provinces = _group_average(rows, "province_name")
    provinces.sort(key=lambda item: str(item["key"] or ""))
    return {
        "report_type": "ministry",
        "start_date": start_date,
        "end_date": end_date,
        "summary": {
            "total_marks": len(rows),
            "total_students": len({r["student_id"] for r in rows}),
            "overall_average_percentage": _avg(
                [r["percentage"] for r in rows]
            ),
        },
        "provinces": [
            {
                "province_name": p["key"],
                "average_percentage": p["average_percentage"],
            }
            for p in provinces
        ],
    }


def province_summary(
    db: Session,
    province_id: uuid.UUID,
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    rows = fetch_marks(db, start_date, end_date, province_id=province_id)
    zones = _group_average(rows, "zone_name")
    zones.sort(key=lambda item: str(item["key"] or ""))
    subjects = _group_average(rows, "subject")
    subjects.sort(key=lambda item: str(item["key"] or ""))
    province_name = next(
        (r["province_name"] for r in rows if r["province_name"]), None
    )
    return {
        "report_type": "province",
        "province_id": province_id,
        "province_name": province_name,
        "start_date": start_date,
        "end_date": end_date,
        "summary": {
            "total_marks": len(rows),
            "total_students": len({r["student_id"] for r in rows}),
            "overall_average_percentage": _avg(
                [r["percentage"] for r in rows]
            ),
        },
        "zones": [
            {
                "zone_name": z["key"],
                "average_percentage": z["average_percentage"],
            }
            for z in zones
        ],
        "subjects": [
            {"subject": s["key"], "average_percentage": s["average_percentage"]}
            for s in subjects
        ],
    }


def zone_summary(
    db: Session, zone_id: uuid.UUID, start_date: date, end_date: date
) -> dict[str, Any]:
    rows = fetch_marks(db, start_date, end_date, zone_id=zone_id)
    schools = _group_average(rows, "school")
    schools.sort(key=lambda item: str(item["key"] or ""))
    subjects = _group_average(rows, "subject")
    subjects.sort(key=lambda item: str(item["key"] or ""))
    zone_name = next((r["zone_name"] for r in rows if r["zone_name"]), None)
    return {
        "report_type": "zone",
        "zone_id": zone_id,
        "zone_name": zone_name,
        "start_date": start_date,
        "end_date": end_date,
        "summary": {
            "total_marks": len(rows),
            "total_students": len({r["student_id"] for r in rows}),
            "overall_average_percentage": _avg(
                [r["percentage"] for r in rows]
            ),
        },
        "schools": [
            {
                "school": s["key"],
                "average_percentage": s["average_percentage"],
            }
            for s in schools
        ],
        "subjects": [
            {"subject": s["key"], "average_percentage": s["average_percentage"]}
            for s in subjects
        ],
        "monthly_trend": monthly_trend(rows),
    }


def school_summary(
    db: Session,
    start_date: date,
    end_date: date,
    *,
    zone_id: uuid.UUID | None = None,
    province_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    rows = fetch_marks(
        db, start_date, end_date, zone_id=zone_id, province_id=province_id
    )
    schools = _group_average(rows, "school")
    schools.sort(key=lambda item: str(item["key"] or ""))
    return {
        "report_type": "school",
        "start_date": start_date,
        "end_date": end_date,
        "summary": {
            "total_marks": len(rows),
            "total_schools": len({r["school"] for r in rows}),
            "overall_average_percentage": _avg(
                [r["percentage"] for r in rows]
            ),
        },
        "schools": [
            {
                "school": s["key"],
                "average_percentage": s["average_percentage"],
            }
            for s in schools
        ],
    }


def _assigned_student_ids(db: Session, teacher_id: uuid.UUID) -> set[uuid.UUID]:
    rows = db.execute(
        select(student_teacher.stid).where(
            student_teacher.tid == teacher_id,
            student_teacher.assignment_status == "approved",
        )
    ).all()
    return {row[0] for row in rows}


def teacher_performance(
    db: Session,
    start_date: date,
    end_date: date,
    *,
    zone_id: uuid.UUID | None = None,
    teacher_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Average marks per teacher based on their approved assigned students."""
    teacher_query = select(Teacher)
    if zone_id is not None:
        teacher_query = teacher_query.where(Teacher.zonal_id == zone_id)
    if teacher_id is not None:
        teacher_query = teacher_query.where(Teacher.tid == teacher_id)
    teachers = list(db.scalars(teacher_query.order_by(Teacher.Name)).all())

    teachers_report: list[dict[str, Any]] = []
    for teacher in teachers:
        assigned = _assigned_student_ids(db, teacher.tid)
        rows: list[dict[str, Any]] = []
        if assigned:
            rows = fetch_marks(db, start_date, end_date, teacher_id=teacher.tid)
            rows = [r for r in rows if r["student_id"] in assigned]
        teachers_report.append(
            {
                "teacher_id": teacher.tid,
                "teacher_name": teacher.Name,
                "subject": teacher.Subject,
                "school": teacher.School,
                "student_count": len(assigned),
                "total_marks": len(rows),
                "average_percentage": _avg([r["percentage"] for r in rows]),
            }
        )
    teachers_report.sort(key=lambda item: item["teacher_name"] or "")
    return {
        "report_type": "teacher_performance",
        "start_date": start_date,
        "end_date": end_date,
        "zone_id": zone_id,
        "teachers": teachers_report,
    }


def student_performance(
    db: Session, student_id: uuid.UUID, start_date: date, end_date: date
) -> dict[str, Any]:
    """A single student's subject and marks with a monthly trend."""
    rows = fetch_marks(
        db, start_date, end_date, student_id=student_id, approved_only=False
    )
    subjects = _group_average(rows, "subject")
    subjects.sort(key=lambda item: str(item["key"] or ""))
    student = db.get(Student, student_id)
    return {
        "report_type": "student_performance",
        "student_id": student_id,
        "student_name": student.Name if student else None,
        "grade": student.Grade if student else None,
        "stream": student.stream if student else None,
        "school": student.School if student else None,
        "start_date": start_date,
        "end_date": end_date,
        "summary": {
            "total_marks": len(rows),
            "overall_average_percentage": _avg(
                [r["percentage"] for r in rows]
            ),
        },
        "subjects": [
            {"subject": s["key"], "average_percentage": s["average_percentage"]}
            for s in subjects
        ],
        "monthly_trend": monthly_trend(rows),
    }


