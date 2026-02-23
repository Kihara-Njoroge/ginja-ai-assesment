from pydantic import BaseModel, UUID4, ConfigDict, Field
from typing import Optional
from datetime import datetime

from app.enums import VerificationTypeEnum


class VerificationTokenSchema(BaseModel):
    token_type: Optional[VerificationTypeEnum]
    is_valid: bool
    token: str
    expires_at: Optional[datetime]
    user_id: UUID4

    model_config = ConfigDict(from_attributes=True, frozen=True)


class VerificationTokenSafeResponse(BaseModel):
    is_valid: bool
    token_type: VerificationTypeEnum
    expires_at: datetime
    is_expired: bool = Field(computed=True)
    can_resend: bool = Field(computed=True)
    remaining_minutes: int = Field(computed=True)

    model_config = ConfigDict(from_attributes=True)


class RequestOTPInput(BaseModel):
    username: str


class ValidateOTPInput(BaseModel):
    username: str
    otp: str


class LoginInput(BaseModel):
    username: str
    password: str


class RefreshTokenInput(BaseModel):
    refresh_token: str
