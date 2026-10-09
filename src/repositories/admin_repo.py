import uuid
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_session
from src.core.security import AuthenticatedPrincipal
from src.models.admin import Admin
from src.models.ministry_officer import MinistryOfficer
from src.models.user_account import UserAccount
from src.repositories._helpers import as_uuid, get_role_id
from src.repositories._pagination import paginate
from src.repositories.account_repo import add_user_account
from src.repositories.report_repo import ReportRepository


class AdminRepository:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.db = db

    def list_admins(self, offset: int, limit: int):
        return paginate(
            self.db,
            select(Admin).order_by(Admin.admin_name, Admin.admin_id),
            offset,
            limit,
        )

    async def addMinistry(self, request_data: dict[str, Any]):
        email = str(request_data.pop("email"))
        password = request_data.pop("password")
        request_data["mini_id"] = uuid.uuid4()
        request_data["role_id"] = get_role_id(self.db, "MINISTRY")
        request_data["approval_status"] = "pending"
        request_data["email"] = email
        officer = MinistryOfficer(**request_data)
        try:
            self.db.add(officer)
            add_user_account(
                self.db,
                actor_type="ministry",
                actor_id=officer.mini_id,
                email=email,
                password=password,
            )
            self.db.commit()
            self.db.refresh(officer)
            return officer
        except Exception:
            self.db.rollback()
            raise

    def get_ministry_officer(self, officer_id: str):
        return self.db.scalar(
            select(MinistryOfficer).where(
                MinistryOfficer.mini_id == as_uuid(officer_id)
            )
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

    def update_ministry_officer(self, officer_id: str, changes: dict[str, Any]):
        officer = self.get_ministry_officer(officer_id)
        if officer is None:
            return None
        try:
            if "email" in changes:
                account = self.db.scalar(
                    select(UserAccount).where(
                        UserAccount.actor_type == "ministry",
                        UserAccount.actor_id == officer.mini_id,
                    )
                )
                if account is not None:
                    account.email = changes["email"].strip().casefold()
                officer.email = changes["email"].strip().casefold()
                changes.pop("email")
            for field, value in changes.items():
                setattr(officer, field, value)
            self.db.commit()
            self.db.refresh(officer)
            return officer
        except Exception:
            self.db.rollback()
            raise

    def delete_ministry_officer(self, officer_id: str):
        officer = self.get_ministry_officer(officer_id)
        if officer is None:
            return False
        try:
            self.db.delete(officer)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def decide_ministry_officer(self, officer_id: str, approved: bool):
        officer = self.get_ministry_officer(officer_id)
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

    def view_any_report(self, principal: AuthenticatedPrincipal):
        return ReportRepository(self.db).list_saved_reports(principal)

    def get_report(self, report_id: uuid.UUID, principal: AuthenticatedPrincipal):
        return ReportRepository(self.db).get_saved_report(report_id, principal)
