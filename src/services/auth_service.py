from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from src.core.database import get_session
from src.repositories.auth_repo import AuthRepository


class AuthService:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.auth_repository = AuthRepository(db)

    def login_with_password(self, email: str, password: str) -> dict[str, Any]:
        return self.auth_repository.login_with_password(email, password)

    def login_with_google_code(
        self, code: str, code_verifier: str, nonce: str
    ) -> dict[str, Any]:
        return self.auth_repository.login_with_google_code(
            code, code_verifier, nonce
        )

    def refresh(self, refresh_token: str) -> dict[str, Any]:
        return self.auth_repository.refresh(refresh_token)

    def logout(self, session_id: UUID) -> None:
        self.auth_repository.logout(session_id)

    def update_password(self, account_id: UUID, password: str) -> None:
        self.auth_repository.update_password(account_id, password)
