from uuid import UUID
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers import user_router
from app.database import get_db
from app.schemas.auth.user_schemas import (
    RegisterInput,
    UserGetSchema,
    UpdateUserInput,
    QueryResp,
    PageInfo,
)
from app.crud.auth.user import (
    get_user_by_id,
    get_users,
    create_user,
    update_user,
    delete_user,
)
from app.models.user import (
    validate_email_unique,
    validate_phone_unique,
    EmailAlreadyExistsError,
    PhoneAlreadyExistsError,
)


@user_router.post("", response_model=UserGetSchema, status_code=201)
async def register_user(user_in: RegisterInput, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    try:
        await validate_email_unique(db, user_in.email)
        if user_in.phone_number:
            await validate_phone_unique(db, user_in.phone_number)
    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PhoneAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user = await create_user(db, user_in)
    return user


@user_router.get("", response_model=QueryResp)
async def list_users(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """Retrieve all users with pagination."""
    users = list(await get_users(db, skip=skip, limit=limit))
    page_info = PageInfo(
        total=len(users), page=(skip // limit) + 1 if limit else 1, size=limit, pages=1
    )
    return QueryResp(results=users, page_info=page_info)


@user_router.get("/{user_id}", response_model=UserGetSchema)
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve a specific user by ID."""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@user_router.put("/{user_id}", response_model=UserGetSchema)
async def edit_user(
    user_id: UUID, user_in: UpdateUserInput, db: AsyncSession = Depends(get_db)
):
    """Update a user's details."""
    if user_in.email:
        try:
            await validate_email_unique(db, user_in.email, exclude_user_id=str(user_id))
        except EmailAlreadyExistsError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if user_in.phone_number:
        try:
            await validate_phone_unique(
                db, user_in.phone_number, exclude_user_id=str(user_id)
            )
        except PhoneAlreadyExistsError as e:
            raise HTTPException(status_code=400, detail=str(e))

    user = await update_user(db, user_id, user_in)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@user_router.delete("/{user_id}", status_code=204)
async def remove_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a user."""
    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
