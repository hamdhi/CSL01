import hashlib
import hmac
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from fastapi import HTTPException, status
from google.auth.exceptions import GoogleAuthError, TransportError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.passwords import hash_password, verify_password
from src.core.security import create_token, decode_token, resolve_principal
from src.models.auth_session import AuthSession
from src.models.user_account import UserAccount
from src.repositories.account_repo import normalize_email

logger = logging.getLogger(__name__)


class AuthRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def login_with_password(self, email: str, password: str) -> dict[str, Any]:
        account = self.db.scalar(
            select(UserAccount).where(
                UserAccount.email == normalize_email(email)
            )
        )
        if account is None or account.password_hash is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )
        if not verify_password(password, account.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )
        principal = resolve_principal(self.db, account)
        return self._create_session(account, principal)

    def login_with_google_code(
        self, code: str, code_verifier: str, nonce: str
    ) -> dict[str, Any]:
        client_id = settings.GOOGLE_CLIENT_ID
        client_secret = settings.GOOGLE_CLIENT_SECRET
        if not client_id or not client_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth client credentials are not configured.",
            )
        token_request = UrlRequest(
            "https://oauth2.googleapis.com/token",
            data=urlencode(
                {
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                    "code_verifier": code_verifier,
                }
            ).encode("ascii"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urlopen(token_request, timeout=10) as response:
                token_response = json.loads(response.read())
        except (
            HTTPError,
            URLError,
            TimeoutError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Google sign-in token exchange failed.",
            ) from error
        if not isinstance(token_response, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Google returned an invalid sign-in response.",
            )
        google_id_token = token_response.get("id_token")
        if not isinstance(google_id_token, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google did not return a valid ID token.",
            )
        try:
            claims = id_token.verify_oauth2_token(
                google_id_token,
                GoogleRequest(),
                audience=client_id,
                clock_skew_in_seconds=60,
            )
        except TransportError as error:
            logger.warning(
                "Could not reach Google's token verification service: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "Could not reach Google's token verification service. "
                    "Please try again."
                ),
            ) from error
        except (ValueError, GoogleAuthError) as error:
            logger.warning(
                "Google ID token verification rejected (%s): %s",
                type(error).__name__,
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    "Google returned an ID token that failed verification. "
                    "Please start sign-in again. If this repeats, check the "
                    "application server log for the verification reason."
                ),
            ) from error
        if not hmac.compare_digest(str(claims.get("nonce", "")), nonce):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google sign-in verification failed.",
            )
        email = claims.get("email")
        if (
            not isinstance(email, str)
            or claims.get("email_verified") is not True
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google account must have a verified email address.",
            )
        account = self.db.scalar(
            select(UserAccount).where(
                UserAccount.email == normalize_email(email)
            )
        )
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No account is registered for this Google email.",
            )
        principal = resolve_principal(self.db, account)
        return self._create_session(account, principal)

    def _create_session(self, account: UserAccount, principal) -> dict[str, Any]:
        session_id = uuid.uuid4()
        refresh_expires = timedelta(days=settings.REFRESH_TOKEN_DAYS)
        access_expires = timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
        access_token, access_jti = create_token(
            account_id=account.account_id,
            session_id=session_id,
            actor_id=principal.actor_id,
            role=principal.role,
            token_type="access",
            expires_in=access_expires,
        )
        refresh_token, _ = create_token(
            account_id=account.account_id,
            session_id=session_id,
            actor_id=principal.actor_id,
            role=principal.role,
            token_type="refresh",
            expires_in=refresh_expires,
        )
        login_session = AuthSession(
            session_id=session_id,
            account_id=account.account_id,
            access_jti=access_jti,
            refresh_token_hash=self._hash_token(refresh_token),
            refresh_expires_at=datetime.now(UTC)
            + refresh_expires,
        )
        try:
            self.db.add(login_session)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return self._token_response(
            access_token, refresh_token, account, principal, access_expires
        )

    def refresh(self, refresh_token: str) -> dict[str, Any]:
        claims = decode_token(refresh_token, "refresh")
        try:
            account_id = uuid.UUID(str(claims["sub"]))
            session_id = uuid.UUID(str(claims["sid"]))
        except (KeyError, ValueError) as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token claims are invalid.",
            ) from error

        login_session = self.db.scalar(
            select(AuthSession)
            .where(AuthSession.session_id == session_id)
            .with_for_update()
        )
        if login_session is None or login_session.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh session is no longer active.",
            )
        submitted_hash = self._hash_token(refresh_token)
        if not hmac.compare_digest(
            login_session.refresh_token_hash, submitted_hash
        ):
            login_session.revoked_at = datetime.now(UTC)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token reuse detected; session revoked.",
            )
        account = self.db.get(UserAccount, account_id)
        if account is None or login_session.account_id != account_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account not found.",
            )
        principal = resolve_principal(self.db, account)

        access_expires = timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
        refresh_expires = timedelta(days=settings.REFRESH_TOKEN_DAYS)
        access_token, access_jti = create_token(
            account_id=account.account_id,
            session_id=session_id,
            actor_id=principal.actor_id,
            role=principal.role,
            token_type="access",
            expires_in=access_expires,
        )
        new_refresh_token, _ = create_token(
            account_id=account.account_id,
            session_id=session_id,
            actor_id=principal.actor_id,
            role=principal.role,
            token_type="refresh",
            expires_in=refresh_expires,
        )
        login_session.access_jti = access_jti
        login_session.refresh_token_hash = self._hash_token(
            new_refresh_token
        )
        login_session.refresh_expires_at = (
            datetime.now(UTC) + refresh_expires
        )
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return self._token_response(
            access_token,
            new_refresh_token,
            account,
            principal,
            access_expires,
        )

    def logout(self, session_id: uuid.UUID) -> None:
        login_session = self.db.get(AuthSession, session_id)
        if login_session is not None and login_session.revoked_at is None:
            login_session.revoked_at = datetime.now(UTC)
            self.db.commit()

    def update_password(
        self, account_id: uuid.UUID, password: str
    ) -> None:
        account = self.db.get(UserAccount, account_id)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found.",
            )
        account.password_hash = hash_password(password)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _token_response(
        access_token: str,
        refresh_token: str,
        account: UserAccount,
        principal,
        access_expires: timedelta,
    ) -> dict[str, Any]:
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(access_expires.total_seconds()),
            "account_id": account.account_id,
            "actor_id": principal.actor_id,
            "role": principal.role,
        }
