from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import asc, select
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

router = APIRouter(prefix="/charity_project", tags=["charity_project"])


async def get_project_or_404(
    session: AsyncSession,
    project_id: int,
) -> CharityProject:
    result = await session.execute(
        select(CharityProject).where(CharityProject.id == project_id)
    )
    project: Optional[CharityProject] = result.scalars().first()
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
    stmt = select(CharityProject).where(CharityProject.name == name)
    if exclude_id is not None:
        stmt = stmt.where(CharityProject.id != exclude_id)
    exists = await session.execute(stmt)
    if exists.scalars().first():
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
    result = await session.execute(
        select(CharityProject).order_by(asc(CharityProject.id))
    )
    return result.scalars().all()


@router.post("/", response_model=CharityProjectRead)
async def create_project(
    project_in: CharityProjectCreate,
    session: AsyncSession = Depends(get_async_session),
    superuser=Depends(current_superuser),
):
    # Unique name check
    await ensure_unique_project_name(session, project_in.name)

    project = CharityProject(
        name=project_in.name,
        description=project_in.description,
        full_amount=project_in.full_amount,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)

    # Allocate existing donations to this new project
    await allocate_donations_to_project(session, project)
    await session.commit()
    await session.refresh(project)

    return project


@router.patch("/{project_id}", response_model=CharityProjectRead)
async def update_project(
    project_id: int,
    project_in: CharityProjectUpdate,
    session: AsyncSession = Depends(get_async_session),
    superuser=Depends(current_superuser),
):
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
        project.name = update_data["name"]

    apply_description_update(project, update_data)

    apply_full_amount_update(project, update_data)

    await session.commit()
    await session.refresh(project)
    return project


@router.delete("/{project_id}", response_model=CharityProjectRead)
async def delete_project(
    project_id: int,
    session: AsyncSession = Depends(get_async_session),
    superuser=Depends(current_superuser),
):
    result = await session.execute(
        select(CharityProject).where(CharityProject.id == project_id)
    )
    project: Optional[CharityProject] = result.scalars().first()
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

    await session.delete(project)
    await session.commit()
    return project
