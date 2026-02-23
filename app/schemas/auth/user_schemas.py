import re
import uuid
from typing import Annotated, Optional, List, ClassVar
from pydantic import (
    UUID4,
    ConfigDict,
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)
from app.models.user import UserStatus, UserRole


class PageInfo(BaseModel):
    total: int
    page: int
    size: int
    pages: int


class RegisterInput(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    password: str
    phone_number: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class UserIsSuperUser(BaseModel):
    is_superuser: bool = Field(default=False)

    @field_validator("is_superuser", mode="before")
    @classmethod
    def normalize_is_superuser(cls, value):
        return bool(value)


class UserSchema(UserIsSuperUser):
    id: Annotated[UUID4, str]
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    identifier: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    status: UserStatus
    role: UserRole

    model_config = ConfigDict(from_attributes=True, frozen=True)


class UserGetSchema(UserIsSuperUser):
    id: Annotated[UUID4, str]
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    identifier: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    status: UserStatus
    role: UserRole
    organization: Optional[List[UUID4]] = None

    model_config = ConfigDict(from_attributes=True, frozen=True)


class UserMiniSchema(BaseModel):
    id: Annotated[UUID4, str]
    name: Optional[str] = None
    username: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {"id": str(uuid.uuid4()), "name": "First Last"}},
    )


class UpdateUserInput(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    signature: Optional[str] = None
    profile_picture: Optional[str] = None
    phone_number: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: Optional[str]):
        """Basic email format validation - uniqueness checked in service layer"""
        if value is not None:
            return value.strip().lower()
        return value

    @model_validator(mode="before")
    @classmethod
    def clean_phone_number(cls, values):
        if isinstance(values, dict):
            phone = values.get("phone_number")
            if phone == "":
                values["phone_number"] = None
        return values

    model_config = ConfigDict(str_strip_whitespace=True)


class UpdateUserStatusInput(BaseModel):
    status: UserStatus


class QueryResp(BaseModel):
    results: List[UserGetSchema]
    page_info: PageInfo
