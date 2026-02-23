from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth.user_schemas import RegisterInput, UpdateUserInput


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """Retrieve a user by their ID."""
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Retrieve a user by their email address."""
    query = select(User).where(User.email == email.lower())
    result = await db.execute(query)
    return result.scalars().first()


async def get_user_by_phone(db: AsyncSession, phone_number: str) -> Optional[User]:
    """Retrieve a user by their phone number."""
    query = select(User).where(User.phone_number == phone_number)
    result = await db.execute(query)
    return result.scalars().first()


async def get_users(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> Sequence[User]:
    """Retrieve a list of users."""
    query = select(User).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def create_user(db: AsyncSession, user_in: RegisterInput) -> User:
    """Create a new user."""
    # Create the user instance
    user = User(
        email=user_in.email,
        phone_number=user_in.phone_number,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        status=user_in.status,
    )

    # Hash and set the password using the complex set_password method
    user.set_password(user_in.password)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession, user_id: UUID, user_in: UpdateUserInput
) -> Optional[User]:
    """Update a user."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    update_data = user_in.model_dump(exclude_unset=True)

    # Exclude fields from the schema that don't exist in the model
    valid_fields = ["first_name", "last_name", "email", "phone_number"]

    for field in valid_fields:
        if field in update_data:
            setattr(user, field, update_data[field])

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: UUID) -> bool:
    """Delete a user."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return False

    await db.delete(user)
    await db.commit()
    return True
