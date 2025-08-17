from fastapi import FastAPI

# Импортируем настройки проекта из config.py.
from app.core.config import settings

from app.models import charity_project, donation  # noqa: F401
# Важно: импортируем модель пользователя, чтобы таблица создавалась в тестах
from app.models import auth_user  # noqa: F401

# Устанавливаем заголовок приложения при помощи аргумента title,
# в качестве значения указываем атрибут app_title объекта settings.
app = FastAPI(title=settings.app_title, description=settings.app_description)

# Import models to ensure they are registered with SQLAlchemy Base
# before metadata.create_all is called in tests.


# Routers
from app.api.endpoints.charity_project import (  # noqa: E402
    router as charity_project_router,
)
from app.api.endpoints.donation import (  # noqa: E402
    router as donation_router,
)
from app.api.endpoints.auth import (  # noqa: E402
    router as auth_router,
)

app.include_router(auth_router)
app.include_router(charity_project_router)
app.include_router(donation_router)