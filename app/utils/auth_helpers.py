import base64
from datetime import datetime, timedelta, timezone
from hashlib import sha1
from typing import Literal, TypedDict, Optional
from uuid import UUID

from fastapi import HTTPException, status
from jose import exceptions, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.crud.auth.user import get_user_by_email, get_user_by_phone
from app.crud.auth.verification import verify_otp, set_otp_as_used
from app.models.user import User
from app.models.token import VerificationToken
from app.enums import VerificationTypeEnum, UserStatus

from fastapi import Depends
from app.utils.security import oauth2_scheme
from app.database import get_db

settings = get_settings()


class TokenType(TypedDict):
    user_id: str
    exp: int
    type: Literal["access", "refresh"]


def get_session_id_for_user(user: User) -> str:
    now = datetime.now(timezone.utc).timestamp()
    content = f"{user.id}{now}".encode()
    return sha1(content).hexdigest()


async def get_user_by_phone_or_email(
    db: AsyncSession, identifier: str
) -> Optional[User]:
    if "@" in identifier:
        return await get_user_by_email(db, identifier)
    return await get_user_by_phone(db, identifier)


async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user_by_phone_or_email(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.status == UserStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is inactive"
        )

    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is suspended"
        )

    if not user.check_password(password) or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    return user


async def authenticate_user_via_otp(db: AsyncSession, username: str, otp: str):
    user = await get_user_by_phone_or_email(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.status == UserStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is inactive"
        )

    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is suspended"
        )

    # Get the latest OTP
    stmt = (
        select(VerificationToken)
        .where(VerificationToken.user_id == user.id)
        .where(VerificationToken.token_type == VerificationTypeEnum.LOGIN)
        .where(VerificationToken.is_valid.is_(True))
        .order_by(VerificationToken.expires_at.desc())
    )
    result = await db.execute(stmt)
    token = result.scalars().first()

    if not token or token.is_expired or not verify_otp(token.token, otp):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP"
        )

    # Mark the OTP as used on successful authentication
    token = await set_otp_as_used(db, token)

    return user


def create_access_token(
    user: User, session_id: str, client_id: str = None, user_info: bytes = None
):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    if user_info:
        user_info = base64.b64encode(user_info).decode("utf-8")

    to_encode = {
        "user_id": str(user.id),
        "exp": expire,
        "type": "access",
        "session_id": session_id,
        "user_info": user_info,
    }

    if client_id:
        to_encode["client_id"] = client_id

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(user: User, session_id: str, client_id: str = None):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {
        "user_id": str(user.id),
        "exp": expire,
        "type": "refresh",
        "session_id": session_id,
    }

    if client_id:
        to_encode["client_id"] = client_id

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def update_access_token(token: str, force_access=True, force_refresh=False, **kwargs):
    decoded = decode_token(token, force_access, force_refresh)
    decoded.update(**kwargs)
    encoded = jwt.encode(decoded, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded


def decode_token(token, force_access=True, force_refresh=False):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        _type = payload.get("type", None)

        if (_type != "access" and force_access and not force_refresh) or (
            _type != "refresh" and force_refresh
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        return payload
    except exceptions.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except exceptions.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


def get_current_user_id(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token, force_access=True)
    user_id: str = payload.get("user_id")
    return user_id


async def get_auth_user(
    current_user: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    from app.crud.auth.user import get_user_by_id

    user = await get_user_by_id(db, UUID(current_user))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User unauthenticated!",
        )
    return user


def get_auth_headers(token: str = Depends(oauth2_scheme)) -> dict:
    return {"Authorization": f"Bearer {token}", "Client-Name": "INNOVEX"}
