"""CRUD operations for claims."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.claim import Claim
from app.models.member import Member
from app.enums import ClaimStatus
from app.utils.claim_validator import ClaimValidator, ClaimValidationError


async def create_claim(
    db: AsyncSession,
    member_id: str,
    provider_id: str,
    diagnosis_code: str,
    procedure_code: str,
    claim_amount: Decimal,
    notes: str | None = None,
) -> Claim:
    """
    Create and process a new claim.

    Validates member eligibility, benefit coverage, and fraud signals.
    """
    validator = ClaimValidator(db)

    # Validate and process claim
    try:
        (
            status,
            approved_amount,
            fraud_flag,
            fraud_reason,
        ) = await validator.validate_and_process_claim(
            member_id=member_id,
            provider_id=provider_id,
            diagnosis_code=diagnosis_code,
            procedure_code=procedure_code,
            claim_amount=claim_amount,
        )
    except ClaimValidationError as e:
        # Create rejected claim with validation error
        claim = Claim(
            member_id=member_id,
            provider_id=provider_id,
            diagnosis_code=diagnosis_code,
            procedure_code=procedure_code,
            claim_amount=claim_amount,
            approved_amount=Decimal("0.00"),
            status=ClaimStatus.REJECTED,
            fraud_flag=False,
            fraud_reason=str(e),
            notes=notes,
            processed_at=datetime.utcnow(),
        )
        db.add(claim)
        await db.flush()
        await db.refresh(claim)
        return claim

    # Create approved/partial claim
    claim = Claim(
        member_id=member_id,
        provider_id=provider_id,
        diagnosis_code=diagnosis_code,
        procedure_code=procedure_code,
        claim_amount=claim_amount,
        approved_amount=approved_amount,
        status=status,
        fraud_flag=fraud_flag,
        fraud_reason=fraud_reason,
        notes=notes,
        processed_at=datetime.utcnow(),
    )

    db.add(claim)
    await db.flush()

    # Update member's used benefit if approved
    if status in [ClaimStatus.APPROVED, ClaimStatus.PARTIAL]:
        result = await db.execute(select(Member).where(Member.id == member_id))
        member = result.scalars().first()
        if member:
            member.used_benefit += approved_amount

    await db.refresh(claim)
    return claim


async def get_claim_by_id(db: AsyncSession, claim_id: UUID) -> Claim | None:
    """Retrieve a claim by ID with relationships loaded."""
    result = await db.execute(
        select(Claim)
        .options(selectinload(Claim.member), selectinload(Claim.provider))
        .where(Claim.id == claim_id)
    )
    return result.scalars().first()


async def list_claims(
    db: AsyncSession,
    member_id: str | None = None,
    provider_id: str | None = None,
    status: ClaimStatus | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Claim], int]:
    """
    List claims with optional filters and pagination.

    Returns:
        Tuple of (claims list, total count)
    """
    query = select(Claim).options(
        selectinload(Claim.member), selectinload(Claim.provider)
    )

    # Apply filters
    if member_id:
        query = query.where(Claim.member_id == member_id)
    if provider_id:
        query = query.where(Claim.provider_id == provider_id)
    if status:
        query = query.where(Claim.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(Claim.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    claims = result.scalars().all()

    return list(claims), total
