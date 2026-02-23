from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any
from fastapi import HTTPException, status


async def create_update_delete_handler(
    model,
    db: AsyncSession,
    data: Any = None,
    method="create",
    query=None,
    schema: Any = None,
):
    response = None
    record = None

    try:
        if query:
            stmt = select(model)
            for key, value in query.items():
                stmt = stmt.filter(getattr(model, key) == value)
            result = await db.execute(stmt)
            record = result.scalars().first()

        if method == "create":
            if record:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Record already found",
                )
            # Support both Pydantic schemas and raw dictionaries
            create_data = data.model_dump() if hasattr(data, "model_dump") else data
            record = model(**create_data)
            db.add(record)
            await db.commit()
            await db.refresh(record)
            response = schema.model_validate(record) if schema else record

        if method == "update":
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Record not found",
                )
            update_data = (
                data.model_dump(exclude_unset=True)
                if hasattr(data, "model_dump")
                else data
            )
            for key, value in update_data.items():
                if value is not None:
                    setattr(record, key, value)
            await db.commit()
            await db.refresh(record)
            response = schema.model_validate(record) if schema else record

        if method == "delete":
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Record not found",
                )

            # Handle soft delete if status field exists, else hard delete
            if hasattr(record, "status"):
                record.status = "DELETED"
                await db.commit()
                await db.refresh(record)
            else:
                await db.delete(record)
                await db.commit()

        return response
    except Exception as e:
        # In production we might want to log this instead of blindly re-raising
        raise e
