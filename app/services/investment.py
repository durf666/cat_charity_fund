from datetime import datetime
from typing import Iterable

from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.charity_project import CharityProject
from app.models.donation import Donation


def now_truncated_to_seconds() -> datetime:
    return datetime.now().replace(microsecond=0)


async def allocate_donations_to_project(
    session: AsyncSession,
    project: CharityProject,
) -> None:
    if project.fully_invested:
        return
    needed = project.full_amount - project.invested_amount
    if needed <= 0:
        project.fully_invested = True
        project.close_date = now_truncated_to_seconds()
        return

    result = await session.execute(
        select(Donation)
        .where(Donation.fully_invested.is_(False))
        .order_by(asc(Donation.create_date), asc(Donation.id))
    )
    donations: Iterable[Donation] = result.scalars().all()
    for donation in donations:
        if needed <= 0:
            break
        available = donation.full_amount - donation.invested_amount
        if available <= 0:
            continue
        to_invest = min(available, needed)
        donation.invested_amount += to_invest
        project.invested_amount += to_invest
        needed -= to_invest

        if donation.invested_amount >= donation.full_amount:
            donation.fully_invested = True
            donation.close_date = now_truncated_to_seconds()

    if project.invested_amount >= project.full_amount:
        project.fully_invested = True
        project.close_date = now_truncated_to_seconds()


async def allocate_projects_for_donation(
    session: AsyncSession,
    donation: Donation,
) -> None:
    if donation.fully_invested:
        return
    available = donation.full_amount - donation.invested_amount
    if available <= 0:
        donation.fully_invested = True
        donation.close_date = now_truncated_to_seconds()
        return

    result = await session.execute(
        select(CharityProject)
        .where(CharityProject.fully_invested.is_(False))
        .order_by(asc(CharityProject.create_date), asc(CharityProject.id))
    )
    projects: Iterable[CharityProject] = result.scalars().all()
    for project in projects:
        if available <= 0:
            break
        needed = project.full_amount - project.invested_amount
        if needed <= 0:
            continue
        to_invest = min(available, needed)
        project.invested_amount += to_invest
        donation.invested_amount += to_invest
        available -= to_invest

        if project.invested_amount >= project.full_amount:
            project.fully_invested = True
            project.close_date = now_truncated_to_seconds()

    if donation.invested_amount >= donation.full_amount:
        donation.fully_invested = True
        donation.close_date = now_truncated_to_seconds()
