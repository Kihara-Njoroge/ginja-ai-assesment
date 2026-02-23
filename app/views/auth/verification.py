import logging
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers import auth_router
from app.schemas.auth.verification import (
    RequestOTPInput,
    ValidateOTPInput,
    LoginInput,
    RefreshTokenInput,
)
from app.utils.auth_helpers import (
    authenticate_user,
    authenticate_user_via_otp,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_session_id_for_user,
    get_user_by_phone_or_email,
)
from app.crud.auth.verification import create_otp_for_user

logger = logging.getLogger(__name__)


@auth_router.post("/verify/request", status_code=status.HTTP_200_OK)
async def request_otp(
    payload: RequestOTPInput,
    db: AsyncSession = Depends(get_db),
):
    """
    Request a new OTP for login/verification.
    Username can be either an email address or a phone number.
    """
    user = await get_user_by_phone_or_email(db, payload.username)
    if not user:
        # We don't want to leak whether a user exists or not for security reasons.
        return {"message": "If the username exists, an OTP has been sent."}

    # Generate a new OTP token
    token, otp_code = await create_otp_for_user(
        db=db, user=user, client_token_expiry=10  # 10 minutes expiry
    )

    # TODO: Integrate an email/SMS provider here to physically send the `otp_code`.
    # For now, we print it to the console/logger strictly for development visibility.
    logger.info(f"Generated OTP for {payload.username}: {otp_code}")

    return {"message": "If the username exists, an OTP has been sent."}


@auth_router.post("/verify/validate", status_code=status.HTTP_200_OK)
async def validate_otp(
    payload: ValidateOTPInput,
    db: AsyncSession = Depends(get_db),
):
    """
    Validate an OTP to authenticate the user and return JWT access/refresh tokens.
    """
    user = await authenticate_user_via_otp(
        db, username=payload.username, otp=payload.otp
    )

    session_id = get_session_id_for_user(user)

    access_token = create_access_token(user, session_id=session_id)
    refresh_token = create_refresh_token(user, session_id=session_id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@auth_router.post("/verify/resend", status_code=status.HTTP_200_OK)
async def resend_otp(
    payload: RequestOTPInput,
    db: AsyncSession = Depends(get_db),
):
    """
    Resend an OTP. Identical in shape to /request, but explicitly defined
    for client logic separation.
    """
    user = await get_user_by_phone_or_email(db, payload.username)
    if not user:
        return {"message": "If the username exists, an OTP has been sent."}

    # Generate a new OTP token
    token, otp_code = await create_otp_for_user(
        db=db, user=user, client_token_expiry=10
    )

    logger.info(f"Resent OTP for {payload.username}: {otp_code}")

    return {"message": "If the username exists, an OTP has been sent."}


@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(
    payload: LoginInput,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate a user using their username (email/phone) and password.
    Returns JWT access and refresh tokens.
    """
    user = await authenticate_user(
        db, username=payload.username, password=payload.password
    )

    session_id = get_session_id_for_user(user)

    access_token = create_access_token(user, session_id=session_id)
    refresh_token = create_refresh_token(user, session_id=session_id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@auth_router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_access_token(
    payload: RefreshTokenInput,
    db: AsyncSession = Depends(get_db),
):
    """
    Issue a new access token using a valid refresh token.
    """
    # decode_token dynamically enforces force_refresh=True checking the `type` claim
    token_data = decode_token(
        payload.refresh_token, force_access=False, force_refresh=True
    )

    user_id = token_data.get("user_id")
    # To maintain statelessness but enforce strict security, ensure user is still active
    from app.crud.auth.user import get_user_by_id
    from uuid import UUID
    from app.enums import UserStatus

    user = await get_user_by_id(db, UUID(user_id))

    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or deleted"
        )

    # Issue a new access token while preserving the original session ID
    session_id = token_data.get("session_id")

    access_token = create_access_token(user, session_id=session_id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
