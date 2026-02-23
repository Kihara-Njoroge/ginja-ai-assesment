import logging
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers import auth_router
from app.schemas.auth.verification import RequestOTPInput, ValidateOTPInput
from app.utils.auth_helpers import (
    authenticate_user_via_otp,
    create_access_token,
    create_refresh_token,
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
    Identifier can be either an email address or a phone number.
    """
    user = await get_user_by_phone_or_email(db, payload.identifier)
    if not user:
        # We don't want to leak whether a user exists or not for security reasons.
        return {"message": "If the identifier exists, an OTP has been sent."}

    # Generate a new OTP token
    token, otp_code = await create_otp_for_user(
        db=db, user=user, client_token_expiry=10  # 10 minutes expiry
    )

    # TODO: Integrate an email/SMS provider here to physically send the `otp_code`.
    # For now, we print it to the console/logger strictly for development visibility.
    logger.info(f"Generated OTP for {payload.identifier}: {otp_code}")

    return {"message": "If the identifier exists, an OTP has been sent."}


@auth_router.post("/verify/validate", status_code=status.HTTP_200_OK)
async def validate_otp(
    payload: ValidateOTPInput,
    db: AsyncSession = Depends(get_db),
):
    """
    Validate an OTP to authenticate the user and return JWT access/refresh tokens.
    """
    user = await authenticate_user_via_otp(
        db, identifier=payload.identifier, otp=payload.otp
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
    user = await get_user_by_phone_or_email(db, payload.identifier)
    if not user:
        return {"message": "If the identifier exists, an OTP has been sent."}

    # Generate a new OTP token
    token, otp_code = await create_otp_for_user(
        db=db, user=user, client_token_expiry=10
    )

    logger.info(f"Resent OTP for {payload.identifier}: {otp_code}")

    return {"message": "If the identifier exists, an OTP has been sent."}
