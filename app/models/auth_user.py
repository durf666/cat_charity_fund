from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.core.db import Base
from app.core.constants import EMAIL_MAX_LEN, PASSWORD_HASH_MAX_LEN


class AuthUser(Base):
    __tablename__ = 'auth_user'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(
        String(EMAIL_MAX_LEN),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password = Column(String(PASSWORD_HASH_MAX_LEN), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    is_superuser = Column(Boolean, nullable=False, default=False)
    is_verified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
