from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.passwords import hash_password
from src.models.user_account import UserAccount


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def add_user_account(
    db: Session,
    actor_type: str,
    actor_id: UUID,
    email: str,
    password: str,
) -> UserAccount:
    normalized_email = normalize_email(email)
    existing_account = db.scalar(
        select(UserAccount.account_id).where(
            UserAccount.email == normalized_email
        )
    )
    if existing_account is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    account = UserAccount(
        actor_type=actor_type,
        actor_id=actor_id,
        email=normalized_email,
        password_hash=hash_password(password),
    )
    db.add(account)
    return account
