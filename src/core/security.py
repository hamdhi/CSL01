import uuid
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import get_session
from src.models.admin import Admin
from src.models.auth_session import AuthSession
from src.models.ministry_officer import MinistryOfficer
from src.models.role import Role
from src.models.student import Student
from src.models.teacher import Teacher
from src.models.user_account import UserAccount
from src.models.zonal_officer import ZonalOfficer

bearer_scheme = HTTPBearer(auto_error=False)
JWT_ISSUER = "csl01"
JWT_AUDIENCE = "csl01-api"
JWT_ALGORITHM = "HS256"


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    account_id: uuid.UUID
    actor_id: uuid.UUID
    actor_type: str
    role: str
    session_id: uuid.UUID | None = None
    zone_id: uuid.UUID | None = None


def create_token(
    *,
    account_id: uuid.UUID,
    session_id: uuid.UUID,
    actor_id: uuid.UUID,
    role: str,
    token_type: str,
    expires_in: timedelta,
    token_id: uuid.UUID | None = None,
) -> tuple[str, str]:
    secret = settings.JWT_SECRET_KEY
    if secret is None or len(secret.encode("utf-8")) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT_SECRET_KEY must be configured with at least 32 bytes.",
        )
    jti = str(token_id or uuid.uuid4())
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": str(account_id),
            "sid": str(session_id),
            "actor_id": str(actor_id),
            "role": role,
            "type": token_type,
            "jti": jti,
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE,
            "iat": now,
            "exp": now + expires_in,
        },
        secret,
        algorithm=JWT_ALGORITHM,
    )
    return token, jti


def decode_token(token: str, expected_type: str) -> dict[str, object]:
    secret = settings.JWT_SECRET_KEY
    if secret is None or len(secret.encode("utf-8")) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT_SECRET_KEY must be configured with at least 32 bytes.",
        )
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options={"require": ["sub", "sid", "jti", "type", "exp", "iat"]},
        )
    except jwt.InvalidTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    if claims.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return claims


def resolve_principal(
    db: Session, account: UserAccount
) -> AuthenticatedPrincipal:
    actor_models = {
        "admin": (Admin, "admin_id", None),
        "ministry": (MinistryOfficer, "mini_id", "approval_status"),
        "zonal": (ZonalOfficer, "zonal_id", "approval_status"),
        "teacher": (Teacher, "tid", "approval_status"),
        "student": (Student, "stid", "registration_status"),
    }
    actor_config = actor_models.get(account.actor_type)
    if actor_config is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account role is invalid.",
        )
    model, id_field, approval_field = actor_config
    actor = db.scalar(
        select(model).where(
            getattr(model, id_field) == account.actor_id
        )
    )
    if actor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account profile was not found.",
        )
    if (
        approval_field is not None
        and getattr(actor, approval_field) != "approved"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is awaiting approval.",
        )
    role_id = actor.role_id
    role = db.get(Role, role_id) if role_id is not None else None
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account role has not been configured.",
        )
    return AuthenticatedPrincipal(
        account_id=account.account_id,
        actor_id=getattr(actor, id_field),
        actor_type=account.actor_type,
        role=role.name,
        zone_id=getattr(actor, "zone_id", None)
        if account.actor_type == "zonal"
        else getattr(actor, "zonal_id", None)
        if account.actor_type == "teacher"
        else getattr(actor, "zone_id", None)
        if account.actor_type == "student"
        else None,
    )


def get_current_principal(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    db: Annotated[Session, Depends(get_session)],
) -> AuthenticatedPrincipal:
    access_token = (
        credentials.credentials
        if credentials is not None
        else request.cookies.get("access_token")
    )
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    claims = decode_token(access_token, "access")
    try:
        account_id = uuid.UUID(str(claims["sub"]))
        session_id = uuid.UUID(str(claims["sid"]))
    except (KeyError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    login_session = db.get(AuthSession, session_id)
    if (
        login_session is None
        or login_session.account_id != account_id
        or login_session.revoked_at is not None
        or login_session.access_jti != claims.get("jti")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This login session is no longer active.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    account = db.get(UserAccount, account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return replace(
        resolve_principal(db, account),
        session_id=session_id,
    )


def require_roles(*allowed_roles: str) -> Callable:
    def role_dependency(
        principal: Annotated[
            AuthenticatedPrincipal, Depends(get_current_principal)
        ],
    ) -> AuthenticatedPrincipal:
        if principal.role != "ADMIN" and principal.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return principal

    return role_dependency
