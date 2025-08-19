from typing import List

from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.donation import Donation


class CRUDDonation(CRUDBase[Donation]):
    async def get_by_user(
        self, session: AsyncSession, user_id: int
    ) -> List[Donation]:
        result = await session.execute(
            select(Donation)
            .where(Donation.user_id == user_id)
            .order_by(asc(Donation.id))
        )
        return list(result.scalars().all())

    async def get_open_ordered(self, session: AsyncSession) -> List[Donation]:
        result = await session.execute(
            select(Donation)
            .where(Donation.fully_invested.is_(False))
            .order_by(asc(Donation.create_date), asc(Donation.id))
        )
        return list(result.scalars().all())


donation_crud = CRUDDonation(Donation)
