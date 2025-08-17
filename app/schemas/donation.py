from datetime import datetime
from typing import Optional

from pydantic import BaseModel, conint


class DonationCreate(BaseModel):
    full_amount: conint(strict=True, gt=0)
    comment: Optional[str] = None

    class Config:
        extra = 'forbid'


class DonationRead(BaseModel):
    id: int
    full_amount: int
    create_date: datetime
    comment: Optional[str] = None

    class Config:
        orm_mode = True


class DonationAdminRead(BaseModel):
    id: int
    user_id: int
    comment: Optional[str] = None
    full_amount: int
    invested_amount: int
    fully_invested: bool
    create_date: datetime
    close_date: Optional[datetime] = None

    class Config:
        orm_mode = True
