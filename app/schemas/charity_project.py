from datetime import datetime
from typing import Optional

from pydantic import BaseModel, conint, constr


class CharityProjectCreate(BaseModel):
    name: constr(min_length=1, max_length=100)
    description: constr(min_length=1)
    full_amount: conint(strict=True, gt=0)

    class Config:
        extra = 'forbid'


class CharityProjectUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=100)] = None
    description: Optional[constr(min_length=1)] = None
    full_amount: Optional[conint(strict=True, gt=0)] = None

    class Config:
        extra = 'forbid'


class CharityProjectRead(BaseModel):
    id: int
    name: str
    description: str
    full_amount: int
    invested_amount: int
    fully_invested: bool
    create_date: datetime
    close_date: Optional[datetime] = None

    class Config:
        orm_mode = True
