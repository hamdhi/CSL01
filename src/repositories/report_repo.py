import uuid
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.core.database import get_session
from src.core.security import AuthenticatedPrincipal
from src.models.educational_zone import EducationalZone
from src.models.monthly_record import MonthlyRecord
from src.models.monthly_record_mark import MonthlyRecordMark
from src.models.province import Province
from src.models.report_snapshot import ReportSnapshot
from src.models.student import Student
from src.repositories._helpers import as_uuid


class ReportRepository:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.db = db

    def get_monthly_records(
        self,
        start_date: date,
        end_date: date,
        report_type: str = "monthly",
        province_id: uuid.UUID | str | None = None,
        zone_id: uuid.UUID | str | None = None,
    ):
        report_types = {
            "monthly",
            "three_month",
            "province",
            "three_month_province",
        }
        if report_type not in report_types:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported report type: {report_type}.",
            )
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="start_date must be on or before end_date.",
            )

        statement = (
            select(MonthlyRecord, Student, EducationalZone, Province)
            .join(Student, Student.stid == MonthlyRecord.fk_stid)
            .outerjoin(
                EducationalZone,
                EducationalZone.zone_id == Student.zone_id,
            )
            .outerjoin(
                Province, Province.prov_id == EducationalZone.prov_id
            )
            .where(
                MonthlyRecord.reporting_month >= start_date,
                MonthlyRecord.reporting_month <= end_date,
            )
            .options(
                selectinload(MonthlyRecord.marks)
                .joinedload(MonthlyRecordMark.subject)
            )
            .order_by(
                MonthlyRecord.reporting_month,
                MonthlyRecord.upload_date,
                MonthlyRecord.id,
            )
        )
        if province_id is not None:
            statement = statement.where(
                EducationalZone.prov_id == as_uuid(province_id)
            )
        if zone_id is not None:
            statement = statement.where(Student.zone_id == as_uuid(zone_id))

        rows = self.db.execute(statement).all()
        records: list[dict[str, Any]] = [
            {
                "id": record.id,
                "fk_stid": record.fk_stid,
                "fk_tid": record.fk_tid,
                "reporting_month": record.reporting_month,
                "upload_date": record.upload_date,
                "approved": record.approved,
                "student_name": student.Name,
                "grade": student.Grade,
                "stream": student.stream,
                "school": student.School,
                "prov_id": zone.prov_id if zone else None,
                "zone_id": student.zone_id,
                "province_name": province.Province_name if province else None,
                "marks": [
                    {
                        "subject_id": mark.subject_id,
                        "subject": mark.subject.name,
                        "score": mark.score,
                        "max_score": mark.max_score,
                        "percentage": (
                            mark.score / mark.max_score * Decimal(100)
                        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                    }
                    for mark in record.marks
                ],
            }
            for record, student, zone, province in rows
        ]

        if report_type in {"province", "three_month_province"}:
            province_reports: dict[uuid.UUID | None, dict[str, Any]] = {}
            subject_reports: dict[
                tuple[uuid.UUID | None, str, uuid.UUID], dict[str, Any]
            ] = {}
            for record in records:
                prov_id = record["prov_id"]
                summary = province_reports.setdefault(
                    prov_id,
                    {
                        "prov_id": prov_id,
                        "province_name": record["province_name"],
                        "total_records": 0,
                        "approved_records": 0,
                        "rejected_records": 0,
                        "pending_records": 0,
                        "subjects": [],
                    },
                )
                summary["total_records"] += 1
                if record["approved"] is True:
                    summary["approved_records"] += 1
                elif record["approved"] is False:
                    summary["rejected_records"] += 1
                else:
                    summary["pending_records"] += 1

                if record["approved"] is not True:
                    continue

                for mark in record["marks"]:
                    subject_key = (
                        prov_id,
                        record["grade"],
                        mark["subject_id"],
                    )
                    subject_summary = subject_reports.setdefault(
                        subject_key,
                        {
                            "prov_id": prov_id,
                            "grade": record["grade"],
                            "subject_id": mark["subject_id"],
                            "subject": mark["subject"],
                            "mark_count": 0,
                            "percentage_total": Decimal(0),
                        },
                    )
                    subject_summary["mark_count"] += 1
                    subject_summary["percentage_total"] += mark["percentage"]

            for subject_summary in subject_reports.values():
                total = subject_summary.pop("percentage_total")
                count = subject_summary["mark_count"]
                subject_summary["average_percentage"] = (
                    total / count
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                province_reports[subject_summary["prov_id"]]["subjects"].append(
                    subject_summary
                )

            for summary in province_reports.values():
                summary["subjects"].sort(
                    key=lambda subject: (
                        subject["grade"],
                        subject["subject"].casefold(),
                    )
                )
            records = sorted(
                province_reports.values(),
                key=lambda report: str(report["province_name"] or ""),
            )

        return {
            "report_type": report_type,
            "start_date": start_date,
            "end_date": end_date,
            "data": records,
        }

    def generate_report(
        self,
        start_date: date,
        end_date: date,
        report_type: str,
        principal: AuthenticatedPrincipal,
    ) -> dict[str, Any]:
        if principal.role == "ZONAL":
            if principal.zone_id is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="The zonal officer is not assigned to a zone.",
                )
            scope_type = "zone"
            scope_id = principal.zone_id
            zone_id = principal.zone_id
        elif principal.role == "MINISTRY":
            scope_type = "province"
            scope_id = None
            zone_id = None
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This role cannot generate this report.",
            )

        report = self.get_monthly_records(
            start_date,
            end_date,
            report_type=report_type,
            zone_id=zone_id,
        )
        snapshot = ReportSnapshot(
            report_type=report_type,
            scope_type=scope_type,
            scope_id=scope_id,
            generated_by_id=principal.account_id,
            start_date=start_date,
            end_date=end_date,
            data=jsonable_encoder(report["data"]),
        )
        try:
            self.db.add(snapshot)
            self.db.commit()
            self.db.refresh(snapshot)
        except Exception:
            self.db.rollback()
            raise
        return {
            "report_id": snapshot.report_id,
            "report_type": snapshot.report_type,
            "scope_type": snapshot.scope_type,
            "scope_id": snapshot.scope_id,
            "start_date": snapshot.start_date,
            "end_date": snapshot.end_date,
            "generated_at": snapshot.generated_at,
            "generated_by_id": snapshot.generated_by_id,
            "data": snapshot.data,
        }

    def list_saved_reports(
        self, principal: AuthenticatedPrincipal
    ) -> list[ReportSnapshot]:
        statement = select(ReportSnapshot)
        if principal.role == "MINISTRY":
            statement = statement.where(
                ReportSnapshot.scope_type == "province"
            )
        elif principal.role == "ZONAL" and principal.zone_id is not None:
            statement = statement.where(
                ReportSnapshot.scope_type == "zone",
                ReportSnapshot.scope_id == principal.zone_id,
            )
        elif principal.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This role cannot view saved reports.",
            )
        return list(
            self.db.scalars(
                statement.order_by(ReportSnapshot.generated_at.desc())
            ).all()
        )

    def get_saved_report(
        self, report_id: uuid.UUID, principal: AuthenticatedPrincipal
    ) -> ReportSnapshot:
        snapshot = self.db.get(ReportSnapshot, report_id)
        if snapshot is None or not self._can_view_snapshot(snapshot, principal):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved report not found.",
            )
        return snapshot

    @staticmethod
    def _can_view_snapshot(
        snapshot: ReportSnapshot, principal: AuthenticatedPrincipal
    ) -> bool:
        if principal.role == "ADMIN":
            return True
        if principal.role == "MINISTRY":
            return snapshot.scope_type == "province"
        return (
            principal.role == "ZONAL"
            and principal.zone_id is not None
            and snapshot.scope_type == "zone"
            and snapshot.scope_id == principal.zone_id
        )