from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.enums import ClaimStatus


class ClaimCreate(BaseModel):
    """Schema for creating a new claim."""

    member_id: str = Field(..., description="Member identifier")
    provider_id: str = Field(..., description="Healthcare provider identifier")
    diagnosis_code: str = Field(..., description="Diagnosis code")
    procedure_code: str = Field(..., description="Procedure code")
    claim_amount: Decimal = Field(..., gt=0, description="Claimed amount")
    notes: str | None = Field(None, description="Additional notes")

    @field_validator("claim_amount")
    @classmethod
    def validate_claim_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Claim amount must be greater than 0")
        if v > Decimal("1000000.00"):
            raise ValueError("Claim amount exceeds maximum allowed")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "member_id": "M123",
                    "provider_id": "H456",
                    "diagnosis_code": "D001",
                    "procedure_code": "P001",
                    "claim_amount": 50000,
                }
            ]
        }
    }


class ClaimResponse(BaseModel):
    """Schema for claim response."""

    claim_id: UUID = Field(..., description="Unique claim identifier")
    member_id: str
    provider_id: str
    diagnosis_code: str
    procedure_code: str
    claim_amount: Decimal
    approved_amount: Decimal
    status: ClaimStatus
    fraud_flag: bool
    fraud_reason: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "claim_id": "c789e123-e89b-12d3-a456-426614174000",
                    "member_id": "M123",
                    "provider_id": "H456",
                    "diagnosis_code": "D001",
                    "procedure_code": "P001",
                    "claim_amount": 50000,
                    "approved_amount": 40000,
                    "status": "APPROVED",
                    "fraud_flag": True,
                    "fraud_reason": "Claim amount exceeds 2x average procedure cost",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:05Z",
                    "processed_at": "2024-01-15T10:30:05Z",
                }
            ]
        },
    }


class ClaimListResponse(BaseModel):
    """Schema for paginated claim list response."""

    claims: list[ClaimResponse]
    total: int
    page: int
    page_size: int

    model_config = {"from_attributes": True}
