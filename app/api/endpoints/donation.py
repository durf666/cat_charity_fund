from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.user import current_superuser, current_user
from app.models.donation import Donation
from app.schemas.donation import (
    DonationAdminRead,
    DonationCreate,
    DonationRead,
)
from app.services.investment import allocate_projects_for_donation

router = APIRouter(prefix="/donation", tags=["donation"])


@router.post("/", response_model=DonationRead)
async def create_donation(
    donation_in: DonationCreate,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_user),
):
    donation = Donation(
        user_id=user.id,
        comment=donation_in.comment,
        full_amount=donation_in.full_amount,
    )
    session.add(donation)
    await session.commit()
    await session.refresh(donation)

    await allocate_projects_for_donation(session, donation)
    await session.commit()
    await session.refresh(donation)

    return donation


@router.get("/my", response_model=List[DonationRead])
async def get_my_donations(
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_user),
):
    result = await session.execute(
        select(Donation)
        .where(Donation.user_id == user.id)
        .order_by(asc(Donation.id))
    )
    return result.scalars().all()


@router.get("/", response_model=List[DonationAdminRead])
async def get_all_donations(
    session: AsyncSession = Depends(get_async_session),
    superuser=Depends(current_superuser),
):
    result = await session.execute(select(Donation).order_by(asc(Donation.id)))
    return result.scalars().all()
