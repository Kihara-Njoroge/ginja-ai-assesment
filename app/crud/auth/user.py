from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth.user_schemas import RegisterInput, UpdateUserInput


from app.utils.create_update_delete import create_update_delete_handler


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
    """Create a new user using the generic handler."""
    # Temporarily create a user to validate/hash the password using the complex logic
    temp_user = User()
    temp_user.set_password(user_in.password)

    user_data = user_in.model_dump(exclude={"password"})
    user_data["hashed_password"] = temp_user.hashed_password

    user = await create_update_delete_handler(
        model=User,
        db=db,
        data=user_data,
        method="create",
    )
    return user


async def update_user(
    db: AsyncSession, user_id: UUID, user_in: UpdateUserInput
) -> Optional[User]:
    """Update a user using the generic handler."""
    user = await create_update_delete_handler(
        model=User, db=db, data=user_in, method="update", query={"id": user_id}
    )
    return user


async def delete_user(db: AsyncSession, user_id: UUID) -> bool:
    """Delete a user using the generic handler."""
    await create_update_delete_handler(
        model=User, db=db, method="delete", query={"id": user_id}
    )
    return True
