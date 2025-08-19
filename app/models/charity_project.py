from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.core.db import Base
from app.core.constants import PROJECT_NAME_MAX_LEN


class CharityProject(Base):
    __tablename__ = 'charity_project'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        String(PROJECT_NAME_MAX_LEN),
        unique=True,
        nullable=False,
        index=True,
    )
    description = Column(Text, nullable=False)
    full_amount = Column(Integer, nullable=False)
    invested_amount = Column(Integer, nullable=False, default=0)
    fully_invested = Column(Boolean, nullable=False, default=False)
    create_date = Column(DateTime, nullable=False, default=datetime.now)
    close_date = Column(DateTime, nullable=True)
