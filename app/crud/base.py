from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Base


ModelType = TypeVar("ModelType", bound=Base)


class CRUDBase(Generic[ModelType]):
    """Generic async CRUD helper for SQLAlchemy models."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, session: AsyncSession, id: int) -> Optional[ModelType]:
        result = await session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalars().first()

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[ModelType]:
        stmt = select(self.model).order_by(asc(self.model.id))
        if skip:
            stmt = stmt.offset(skip)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        session: AsyncSession,
        obj_in: Dict[str, Any],
        *,
        commit: bool = True,
        refresh: bool = True,
    ) -> ModelType:
        obj = self.model(**obj_in)
        session.add(obj)
        if commit:
            await session.commit()
            if refresh:
                await session.refresh(obj)
        return obj

    async def update(
        self,
        session: AsyncSession,
        db_obj: ModelType,
        obj_in: Dict[str, Any],
        *,
        commit: bool = True,
        refresh: bool = True,
    ) -> ModelType:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        if commit:
            await session.commit()
            if refresh:
                await session.refresh(db_obj)
        return db_obj

    async def remove(
        self,
        session: AsyncSession,
        id: int,
    ) -> Optional[ModelType]:
        obj = await self.get(session, id)
        if obj is None:
            return None
        await session.delete(obj)
        await session.commit()
        return obj
