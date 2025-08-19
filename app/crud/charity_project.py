from typing import Optional

from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.charity_project import CharityProject


class CRUDCharityProject(CRUDBase[CharityProject]):
    async def get_by_name(
        self, session: AsyncSession, name: str
    ) -> Optional[CharityProject]:
        result = await session.execute(
            select(CharityProject).where(CharityProject.name == name)
        )
        return result.scalars().first()

    async def get_open_ordered(self, session: AsyncSession):
        result = await session.execute(
            select(CharityProject)
            .where(CharityProject.fully_invested.is_(False))
            .order_by(asc(CharityProject.create_date), asc(CharityProject.id))
        )
        return list(result.scalars().all())


charity_project_crud = CRUDCharityProject(CharityProject)
