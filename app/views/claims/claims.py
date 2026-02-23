"""API endpoints for claims management."""

import logging
from uuid import UUID

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers import claims_router
from app.schemas.claims import ClaimCreate, ClaimResponse, ClaimListResponse
from app.crud.claims import create_claim, get_claim_by_id, list_claims
from app.enums import ClaimStatus

logger = logging.getLogger(__name__)


@claims_router.post(
    "",
    response_model=ClaimResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new claim",
    description="Submit a new health insurance claim for validation and processing",
)
async def submit_claim(
    claim_data: ClaimCreate,
    db: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    """
    Submit a new claim for processing.

    The system will:
    1. Validate member eligibility
    2. Validate benefit coverage
    3. Check for fraud signals
    4. Return approval decision (APPROVED/PARTIAL/REJECTED)
    """
    logger.info(
        f"Processing claim submission for member {claim_data.member_id}, "
        f"amount: {claim_data.claim_amount}"
    )

    try:
        claim = await create_claim(
            db=db,
            member_id=claim_data.member_id,
            provider_id=claim_data.provider_id,
            diagnosis_code=claim_data.diagnosis_code,
            procedure_code=claim_data.procedure_code,
            claim_amount=claim_data.claim_amount,
            notes=claim_data.notes,
        )

        logger.info(
            f"Claim {claim.id} processed: status={claim.status.value}, "
            f"approved_amount={claim.approved_amount}, fraud_flag={claim.fraud_flag}"
        )

        return ClaimResponse(
            claim_id=claim.id,
            member_id=claim.member_id,
            provider_id=claim.provider_id,
            diagnosis_code=claim.diagnosis_code,
            procedure_code=claim.procedure_code,
            claim_amount=claim.claim_amount,
            approved_amount=claim.approved_amount,
            status=claim.status,
            fraud_flag=claim.fraud_flag,
            fraud_reason=claim.fraud_reason,
            notes=claim.notes,
            created_at=claim.created_at,
            updated_at=claim.updated_at,
            processed_at=claim.processed_at,
        )

    except Exception as e:
        logger.error(f"Error processing claim: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process claim: {str(e)}",
        )


@claims_router.get(
    "/{claim_id}",
    response_model=ClaimResponse,
    summary="Get claim by ID",
    description="Retrieve detailed information about a specific claim",
)
async def get_claim(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    """Retrieve a claim by its unique identifier."""
    logger.info(f"Retrieving claim {claim_id}")

    claim = await get_claim_by_id(db, claim_id)

    if not claim:
        logger.warning(f"Claim {claim_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found",
        )

    return ClaimResponse(
        claim_id=claim.id,
        member_id=claim.member_id,
        provider_id=claim.provider_id,
        diagnosis_code=claim.diagnosis_code,
        procedure_code=claim.procedure_code,
        claim_amount=claim.claim_amount,
        approved_amount=claim.approved_amount,
        status=claim.status,
        fraud_flag=claim.fraud_flag,
        fraud_reason=claim.fraud_reason,
        notes=claim.notes,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
        processed_at=claim.processed_at,
    )


@claims_router.get(
    "",
    response_model=ClaimListResponse,
    summary="List claims",
    description="List claims with optional filters and pagination",
)
async def list_all_claims(
    member_id: str | None = Query(None, description="Filter by member ID"),
    provider_id: str | None = Query(None, description="Filter by provider ID"),
    status_filter: ClaimStatus | None = Query(
        None, alias="status", description="Filter by claim status"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> ClaimListResponse:
    """
    List claims with optional filtering and pagination.

    Supports filtering by:
    - member_id: Filter claims for a specific member
    - provider_id: Filter claims from a specific provider
    - status: Filter by claim status (PENDING, APPROVED, PARTIAL, REJECTED)
    """
    skip = (page - 1) * page_size

    logger.info(
        f"Listing claims: member_id={member_id}, provider_id={provider_id}, "
        f"status={status_filter}, page={page}, page_size={page_size}"
    )

    claims, total = await list_claims(
        db=db,
        member_id=member_id,
        provider_id=provider_id,
        status=status_filter,
        skip=skip,
        limit=page_size,
    )

    claims_response = [
        ClaimResponse(
            claim_id=claim.id,
            member_id=claim.member_id,
            provider_id=claim.provider_id,
            diagnosis_code=claim.diagnosis_code,
            procedure_code=claim.procedure_code,
            claim_amount=claim.claim_amount,
            approved_amount=claim.approved_amount,
            status=claim.status,
            fraud_flag=claim.fraud_flag,
            fraud_reason=claim.fraud_reason,
            notes=claim.notes,
            created_at=claim.created_at,
            updated_at=claim.updated_at,
            processed_at=claim.processed_at,
        )
        for claim in claims
    ]

    return ClaimListResponse(
        claims=claims_response,
        total=total,
        page=page,
        page_size=page_size,
    )
