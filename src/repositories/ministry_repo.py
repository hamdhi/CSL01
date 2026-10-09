import uuid
from datetime import date
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.database import get_session
from src.models.educational_zone import EducationalZone
from src.models.ministry_officer import MinistryOfficer
from src.models.province import Province
from src.models.subject import Subject
from src.models.zonal_officer import ZonalOfficer
from src.repositories._helpers import as_uuid, get_role_id
from src.repositories._pagination import paginate
from src.repositories.account_repo import add_user_account
from src.repositories.report_repo import ReportRepository


class MinistryRepository:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.db = db

    @staticmethod
    def _subject_name_key(name: str) -> str:
        return " ".join(name.split()).casefold()

    def create_subject(self, request_data: dict[str, Any]):
        name = " ".join(request_data["name"].split())
        grade = request_data["grade"].strip()
        stream = " ".join(request_data["stream"].split()).casefold()
        name_key = self._subject_name_key(name)
        if grade not in {str(value) for value in range(1, 14)}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="grade must be from 1 through 13.",
            )
        if grade not in {"12", "13"} and stream:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A stream can only be assigned for Grades 12 or 13.",
            )
        if not name_key:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Subject name cannot be blank.",
            )
        subject = Subject(
            name=name,
            name_key=name_key,
            grade=grade,
            stream=stream,
            active=True,
        )
        try:
            self.db.add(subject)
            self.db.commit()
            self.db.refresh(subject)
            return subject
        except IntegrityError as error:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This subject already exists for the grade and stream.",
            ) from error
        except Exception:
            self.db.rollback()
            raise

    def list_subjects(
        self,
        grade: str | None = None,
        stream: str | None = None,
        include_inactive: bool = False,
    ):
        statement = select(Subject)
        if grade is not None:
            statement = statement.where(Subject.grade == grade)
        if stream is not None:
            statement = statement.where(Subject.stream == stream)
        if not include_inactive:
            statement = statement.where(Subject.active.is_(True))
        return list(self.db.scalars(statement.order_by(Subject.grade, Subject.stream, Subject.name)).all())

    def create_zone(
        self, name: str, prov_id: uuid.UUID
    ) -> EducationalZone:
        normalized_name = " ".join(name.split())
        if not normalized_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Zone name cannot be blank.",
            )
        if self.db.get(Province, prov_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Province not found.",
            )
        zone = EducationalZone(
            zone_id=uuid.uuid4(),
            name=normalized_name,
            prov_id=prov_id,
        )
        try:
            self.db.add(zone)
            self.db.commit()
            self.db.refresh(zone)
            return zone
        except IntegrityError as error:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A zone with this name already exists.",
            ) from error
        except Exception:
            self.db.rollback()
            raise

    def list_zones(self, offset: int, limit: int):
        return paginate(
            self.db,
            select(EducationalZone).order_by(
                EducationalZone.prov_id,
                EducationalZone.name,
                EducationalZone.zone_id,
            ),
            offset,
            limit,
        )

    def list_provinces(self, offset: int, limit: int):
        return paginate(
            self.db,
            select(Province).order_by(Province.Province_name, Province.prov_id),
            offset,
            limit,
        )

    def update_subject(self, subject_id: str, changes: dict[str, Any]):
        subject = self.db.get(Subject, as_uuid(subject_id))
        if subject is None:
            return None
        if "name" in changes:
            name = " ".join(changes["name"].split())
            if not name:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Subject name cannot be blank.",
                )
            subject.name = name
            subject.name_key = self._subject_name_key(name)
        if "active" in changes:
            subject.active = changes["active"]
        try:
            self.db.commit()
            self.db.refresh(subject)
            return subject
        except IntegrityError as error:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This subject already exists for the grade and stream.",
            ) from error
        except Exception:
            self.db.rollback()
            raise

    def addZonalOfficer(self, request_data: dict[str, Any]):
        email = str(request_data.pop("email"))
        password = request_data.pop("password")
        ministry_id = request_data.get("mini_id")
        if ministry_id is not None and self.db.get(
            MinistryOfficer, ministry_id
        ) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ministry officer not found.",
            )
        zone_id = request_data.get("zone_id")
        if zone_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A zone must be selected for the zonal officer.",
            )
        if self.db.get(EducationalZone, zone_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Educational zone not found.",
            )
        request_data["zonal_id"] = uuid.uuid4()
        request_data["role_id"] = get_role_id(self.db, "ZONAL")
        request_data["approval_status"] = "pending"
        officer = ZonalOfficer(**request_data)
        try:
            self.db.add(officer)
            add_user_account(
                self.db,
                actor_type="zonal",
                actor_id=officer.zonal_id,
                email=email,
                password=password,
            )
            self.db.commit()
            self.db.refresh(officer)
            return officer
        except Exception:
            self.db.rollback()
            raise

    def get_zonal_officer(self, officer_id: str):
        return self.db.scalar(
            select(ZonalOfficer).where(
                ZonalOfficer.zonal_id == as_uuid(officer_id)
            )
        )

    def list_zonal_officers(
        self, ministry_id: uuid.UUID, offset: int, limit: int
    ):
        return paginate(
            self.db,
            select(ZonalOfficer)
            .where(ZonalOfficer.mini_id == ministry_id)
            .order_by(ZonalOfficer.name, ZonalOfficer.zonal_id),
            offset,
            limit,
        )

    def list_ministry_officers(self, offset: int, limit: int):
        return paginate(
            self.db,
            select(MinistryOfficer).order_by(
                MinistryOfficer.name, MinistryOfficer.mini_id
            ),
            offset,
            limit,
        )

    def update_zonal_officer(self, officer_id: str, changes: dict[str, Any]):
        officer = self.get_zonal_officer(officer_id)
        if officer is None:
            return None
        ministry_id = changes.get("mini_id")
        if ministry_id is not None and self.db.get(
            MinistryOfficer, ministry_id
        ) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ministry officer not found.",
            )
        zone_id = changes.get("zone_id")
        if "zone_id" in changes and zone_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A zone must be selected for the zonal officer.",
            )
        if zone_id is not None and self.db.get(EducationalZone, zone_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Educational zone not found.",
            )
        try:
            for field, value in changes.items():
                setattr(officer, field, value)
            self.db.commit()
            self.db.refresh(officer)
            return officer
        except Exception:
            self.db.rollback()
            raise

    def delete_zonal_officer(self, officer_id: str):
        officer = self.get_zonal_officer(officer_id)
        if officer is None:
            return False
        try:
            self.db.delete(officer)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def decide_zonal_officer(self, officer_id: str, approved: bool):
        officer = self.get_zonal_officer(officer_id)
        if officer is None:
            return None
        try:
            officer.approval_status = "approved" if approved else "rejected"
            self.db.commit()
            self.db.refresh(officer)
            return officer
        except Exception:
            self.db.rollback()
            raise

    def get_monthly_province_report(
        self, start_date: date, end_date: date, principal
    ):
        return ReportRepository(self.db).generate_report(
            start_date, end_date, report_type="province", principal=principal
        )

    def get_three_month_province_report(
        self, start_date: date, end_date: date, principal
    ):
        return ReportRepository(self.db).generate_report(
            start_date,
            end_date,
            report_type="three_month_province",
            principal=principal,
        )
