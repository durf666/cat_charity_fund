from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.user import current_superuser
from app.models.charity_project import CharityProject
from app.schemas.charity_project import (
    CharityProjectCreate,
    CharityProjectRead,
    CharityProjectUpdate,
)
from app.services.investment import allocate_donations_to_project
from app.crud.charity_project import charity_project_crud
from app.crud.donation import donation_crud

router = APIRouter(prefix="/charity_project", tags=["charity_project"])


async def get_project_or_404(
    session: AsyncSession,
    project_id: int,
) -> CharityProject:
    project: Optional[CharityProject] = await charity_project_crud.get(
        session, project_id
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


async def ensure_unique_project_name(
    session: AsyncSession,
    name: str,
    exclude_id: Optional[int] = None,
) -> None:
    existing = await charity_project_crud.get_by_name(session, name)
    if existing and (exclude_id is None or existing.id != exclude_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project name must be unique",
        )


def apply_description_update(
    project: CharityProject,
    update_data: dict,
):
    if "description" in update_data:
        if not update_data["description"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Description must not be empty",
            )
        project.description = update_data["description"]


def apply_full_amount_update(
    project: CharityProject,
    update_data: dict,
):
    if "full_amount" in update_data:
        new_full = update_data["full_amount"]
        if new_full <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="full_amount must be positive",
            )
        if new_full < project.invested_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="full_amount can't be less than invested_amount",
            )
        project.full_amount = new_full
        # Close if fully invested after change
        if (
            project.invested_amount >= project.full_amount and not
            project.fully_invested
        ):
            project.fully_invested = True
            project.close_date = datetime.now().replace(microsecond=0)


@router.get("/", response_model=List[CharityProjectRead])
async def get_projects(
    session: AsyncSession = Depends(get_async_session),
):
    """Получить список всех благотворительных проектов.

    - Доступ: любой пользователь
    - Возвращает: полный список `CharityProjectRead`
    """
    return await charity_project_crud.get_multi(session)


@router.post("/", response_model=CharityProjectRead)
async def create_project(
    project_in: CharityProjectCreate,
    session: AsyncSession = Depends(get_async_session),
    superuser=Depends(current_superuser),
):
    """Создать новый благотворительный проект.

    - Доступ: только суперюзер
    - Проверки: уникальность имени, валидность `full_amount`
    - Инвестиции: сразу после создания распределяются открытые донаты

    Примечание: коммит выполняется один раз — после расчётов инвестирования.
    """
    # Unique name check
    await ensure_unique_project_name(session, project_in.name)

    project = await charity_project_crud.create(
        session,
        {
            "name": project_in.name,
            "description": project_in.description,
            "full_amount": project_in.full_amount,
        },
        commit=False,
        refresh=False,
    )

    # Allocate existing donations to this new project
    donations = await donation_crud.get_open_ordered(session)
    allocate_donations_to_project(project, donations)
    # Persist possible changes after allocation
    project = await charity_project_crud.update(
        session, project, {}, commit=True, refresh=True
    )

    return project


@router.patch("/{project_id}", response_model=CharityProjectRead)
async def update_project(
    project_id: int,
    project_in: CharityProjectUpdate,
    session: AsyncSession = Depends(get_async_session),
    superuser=Depends(current_superuser),
):
    """Обновить параметры проекта.

    - Доступ: только суперюзер
    - Нельзя редактировать закрытый проект
    - `full_amount` не может быть меньше уже инвестированной суммы
    - При достижении цели проект автоматически закрывается
    """
    project = await get_project_or_404(session, project_id)

    if project.fully_invested:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Closed project can't be edited"
        )

    update_data = project_in.dict(exclude_unset=True)

    # Name uniqueness check
    if "name" in update_data:
        await ensure_unique_project_name(
            session, update_data["name"], exclude_id=project.id
        )

    # Description validation is handled by schema; nothing extra here

    # full_amount validation and possible closing
    if "full_amount" in update_data:
        new_full = update_data["full_amount"]
        if new_full < project.invested_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="full_amount can't be less than invested_amount",
            )
        # If closing condition will be achieved after update
        if project.invested_amount >= new_full and not project.fully_invested:
            update_data["fully_invested"] = True
            update_data["close_date"] = datetime.now().replace(microsecond=0)

    project = await charity_project_crud.update(session, project, update_data)
    return project


@router.delete("/{project_id}", response_model=CharityProjectRead)
async def delete_project(
    project_id: int,
    session: AsyncSession = Depends(get_async_session),
    superuser=Depends(current_superuser),
):
    """Удалить проект по `id`.

    - Доступ: только суперюзер
    - Нельзя удалить проект, если он закрыт или в него уже внесены средства
    """
    project: Optional[CharityProject] = await charity_project_crud.get(
        session, project_id
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    if project.fully_invested or project.invested_amount > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can't delete invested/closed project"
        )

    deleted = await charity_project_crud.remove(session, project.id)
    return deleted
