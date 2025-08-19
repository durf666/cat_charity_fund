from datetime import datetime
from typing import Iterable

from app.models.charity_project import CharityProject
from app.models.donation import Donation


def now_truncated_to_seconds() -> datetime:
    return datetime.now().replace(microsecond=0)


def allocate_donations_to_project(
    project: CharityProject,
    donations: Iterable[Donation],
) -> None:
    if project.fully_invested:
        return
    # Coalesce possibly None invested_amount before first commit
    if project.invested_amount is None:
        project.invested_amount = 0
    needed = project.full_amount - project.invested_amount
    if needed <= 0:
        project.fully_invested = True
        project.close_date = now_truncated_to_seconds()
        return

    for donation in donations:
        if needed <= 0:
            break
        if donation.invested_amount is None:
            donation.invested_amount = 0
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


def allocate_projects_for_donation(
    donation: Donation,
    projects: Iterable[CharityProject],
) -> None:
    if donation.fully_invested:
        return
    if donation.invested_amount is None:
        donation.invested_amount = 0
    available = donation.full_amount - donation.invested_amount
    if available <= 0:
        donation.fully_invested = True
        donation.close_date = now_truncated_to_seconds()
        return

    for project in projects:
        if available <= 0:
            break
        if project.invested_amount is None:
            project.invested_amount = 0
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
