"""Business logic for claim validation and fraud detection."""

from decimal import Decimal
from typing import Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.member import Member
from app.models.provider import Provider
from app.models.procedure import Procedure
from app.models.diagnosis import Diagnosis
from app.enums import ClaimStatus, MemberStatus


class ClaimValidationError(Exception):
    """Raised when claim validation fails."""

    pass


class ClaimValidator:
    """Validates claims and detects potential fraud."""

    FRAUD_MULTIPLIER = Decimal("2.0")  # Flag if claim > 2x average cost

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_and_process_claim(
        self,
        member_id: str,
        provider_id: str,
        diagnosis_code: str,
        procedure_code: str,
        claim_amount: Decimal,
    ) -> Tuple[ClaimStatus, Decimal, bool, str | None]:
        """
        Validate claim and return processing decision.

        Returns:
            Tuple of (status, approved_amount, fraud_flag, fraud_reason)
        """
        # 1. Validate member eligibility
        member = await self._validate_member(member_id)

        # 2. Validate provider
        await self._validate_provider(provider_id)

        # 3. Validate diagnosis and procedure codes
        await self._validate_diagnosis(diagnosis_code)
        procedure = await self._validate_procedure(procedure_code)

        # 4. Check for fraud signals
        fraud_flag, fraud_reason = await self._check_fraud(claim_amount, procedure)

        # 5. Determine approval amount and status
        status, approved_amount = self._determine_approval(
            claim_amount, member.remaining_benefit, fraud_flag
        )

        return status, approved_amount, fraud_flag, fraud_reason

    async def _validate_member(self, member_id: str) -> Member:
        """Validate member exists and is eligible."""
        result = await self.db.execute(select(Member).where(Member.id == member_id))
        member = result.scalars().first()

        if not member:
            raise ClaimValidationError(f"Member {member_id} not found")

        if member.status != MemberStatus.ACTIVE:
            raise ClaimValidationError(
                f"Member {member_id} is not active (status: {member.status.value})"
            )

        if member.remaining_benefit <= 0:
            raise ClaimValidationError(
                f"Member {member_id} has exhausted benefit limit"
            )

        return member

    async def _validate_provider(self, provider_id: str) -> Provider:
        """Validate provider exists and is active."""
        result = await self.db.execute(
            select(Provider).where(Provider.id == provider_id)
        )
        provider = result.scalars().first()

        if not provider:
            raise ClaimValidationError(f"Provider {provider_id} not found")

        if not provider.is_active:
            raise ClaimValidationError(f"Provider {provider_id} is not active")

        return provider

    async def _validate_diagnosis(self, diagnosis_code: str) -> Diagnosis:
        """Validate diagnosis code exists."""
        result = await self.db.execute(
            select(Diagnosis).where(Diagnosis.code == diagnosis_code)
        )
        diagnosis = result.scalars().first()

        if not diagnosis:
            raise ClaimValidationError(f"Diagnosis code {diagnosis_code} not found")

        return diagnosis

    async def _validate_procedure(self, procedure_code: str) -> Procedure:
        """Validate procedure code exists."""
        result = await self.db.execute(
            select(Procedure).where(Procedure.code == procedure_code)
        )
        procedure = result.scalars().first()

        if not procedure:
            raise ClaimValidationError(f"Procedure code {procedure_code} not found")

        return procedure

    async def _check_fraud(
        self, claim_amount: Decimal, procedure: Procedure
    ) -> Tuple[bool, str | None]:
        """
        Check for fraud signals.

        Simple rule: Flag if claim amount > 2x average procedure cost.
        """
        threshold = procedure.average_cost * self.FRAUD_MULTIPLIER

        if claim_amount > threshold:
            fraud_reason = (
                f"Claim amount ({claim_amount}) exceeds {self.FRAUD_MULTIPLIER}x "
                f"average procedure cost ({procedure.average_cost})"
            )
            return True, fraud_reason

        return False, None

    def _determine_approval(
        self, claim_amount: Decimal, remaining_benefit: Decimal, fraud_flag: bool
    ) -> Tuple[ClaimStatus, Decimal]:
        """
        Determine claim status and approved amount.

        Logic:
        - If fraud flagged and claim > remaining benefit: REJECTED
        - If claim > remaining benefit: PARTIAL (approve up to remaining)
        - Otherwise: APPROVED (full amount)
        """
        if fraud_flag:
            return ClaimStatus.REJECTED, Decimal("0.00")

        if claim_amount > remaining_benefit:
            return ClaimStatus.PARTIAL, remaining_benefit

        return ClaimStatus.APPROVED, claim_amount
