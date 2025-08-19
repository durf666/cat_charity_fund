from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.user import current_superuser, current_user
from app.schemas.donation import (
    DonationAdminRead,
    DonationCreate,
    DonationRead,
)
from app.services.investment import allocate_projects_for_donation
from app.crud.donation import donation_crud
from app.crud.charity_project import charity_project_crud

router = APIRouter(prefix="/donation", tags=["donation"])


@router.post("/", response_model=DonationRead)
async def create_donation(
    donation_in: DonationCreate,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_user),
):
    """Создать донат текущего пользователя.

    - Доступ: авторизованный пользователь
    - Инвестиции: после создания средства распределяются по открытым проектам
    """
    donation = await donation_crud.create(
        session,
        {
            "user_id": user.id,
            "comment": donation_in.comment,
            "full_amount": donation_in.full_amount,
        },
        commit=False,
        refresh=False,
    )

    projects = await charity_project_crud.get_open_ordered(session)
    allocate_projects_for_donation(donation, projects)
    # Persist potential updates after allocation
    donation = await donation_crud.update(
        session, donation, {}, commit=True, refresh=True
    )

    return donation


@router.get("/my", response_model=List[DonationRead])
async def get_my_donations(
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_user),
):
    """Список донатов текущего пользователя.

    - Доступ: авторизованный пользователь
    """
    return await donation_crud.get_by_user(session, user.id)


@router.get("/", response_model=List[DonationAdminRead])
async def get_all_donations(
    session: AsyncSession = Depends(get_async_session),
    superuser=Depends(current_superuser),
):
    """Список всех донатов (для администраторов).

    - Доступ: только суперюзер
    """
    return await donation_crud.get_multi(session)
