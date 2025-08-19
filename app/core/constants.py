"""Application-wide constants.

Keep all shared configuration-like constants here to avoid duplication
and magic numbers spread across modules.
"""
from typing import Final

# String length limits
EMAIL_MAX_LEN: Final[int] = 320
PASSWORD_HASH_MAX_LEN: Final[int] = 255
PROJECT_NAME_MAX_LEN: Final[int] = 100

# Auth requirements
MIN_PASSWORD_LEN: Final[int] = 3
