import hashlib
import random
from typing import Optional
from datetime import datetime, timezone, timedelta
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.token import VerificationToken
from app.enums import VerificationTypeEnum

logger = logging.getLogger(__name__)


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def generate_verification_otp_for_user(user: User):
    if not user:
        return None
    otp = generate_otp()
    hashed_otp = hash_otp(otp)
    return hashed_otp, otp


async def create_otp_for_user(
    db: AsyncSession,
    user: User,
    token_type=VerificationTypeEnum.INITIAL_VERIFICATION,
    client_token_expiry=60,
):
    hashed_otp, otp = generate_verification_otp_for_user(user)
    expiry_timestamp = datetime.now(timezone.utc) + timedelta(
        minutes=client_token_expiry
    )

    token = VerificationToken(
        user_id=user.id,
        token_type=token_type,
        token=hashed_otp,
        expires_at=expiry_timestamp,
        is_valid=True,
    )
    db.add(token)
    await db.commit()
    await db.refresh(token)

    return token, otp


async def get_otp_by_otp_str(
    db: AsyncSession, hashed_otp: str, safe=True
) -> Optional[VerificationToken]:
    """
    Set safe to false to get token even if expired or used.
    """
    stmt = select(VerificationToken).where(VerificationToken.token == hashed_otp)
    if safe:
        stmt = stmt.where(VerificationToken.expires_at > datetime.now(timezone.utc))
        stmt = stmt.where(VerificationToken.is_valid.is_(True))

    result = await db.execute(stmt)
    return result.scalars().first()


async def refresh_expired_otp(db: AsyncSession, token_id: str, client_token_expiry=60):
    result = await db.execute(
        select(VerificationToken).where(VerificationToken.id == token_id)
    )
    old_token = result.scalars().first()

    if old_token:
        old_token.is_valid = False
        db.add(old_token)
        await db.commit()

        user_result = await db.execute(select(User).where(User.id == old_token.user_id))
        user = user_result.scalars().first()

        hashed_otp, otp = generate_verification_otp_for_user(user)
        expiry_timestamp = datetime.now(timezone.utc) + timedelta(
            minutes=client_token_expiry
        )

        new_token = VerificationToken(
            token=hashed_otp,
            user_id=old_token.user_id,
            token_type=old_token.token_type,
            is_valid=True,
            expires_at=expiry_timestamp,
        )
        db.add(new_token)
        await db.commit()
        await db.refresh(new_token)

        return new_token, otp
    return None, None


async def set_otp_as_used(db: AsyncSession, token: VerificationToken):
    token.is_valid = False
    token.expires_at = datetime.now(timezone.utc)
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token


def verify_otp(stored_hashed_otp: str, submitted_otp: str):
    hashed_submitted_otp = hash_otp(submitted_otp)
    return stored_hashed_otp == hashed_submitted_otp
