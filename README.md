# QRKot Charity Fund Backend

Бэкенд сервиса благотворительных сборов. Построен на FastAPI + SQLAlchemy (async) + Pydantic v1, с автоподбором инвестиций (FIFO) между пожертвованиями и проектами.

## Стек
- FastAPI
- SQLAlchemy 1.4 (async, aiosqlite)
- Pydantic 1.9
- Alembic
- Pytest

## Быстрый старт
1) Установи зависимости (Python 3.10):
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2) Настрой окружение: скопируй `.env.example` → `.env` и при необходимости поправь значения.
```env
APP_TITLE="Пожертвования на благотворительный фонд QRKot"
APP_DESCRIPTION="API сервиса благотворительного фонда QRKot"
DATABASE_URL="sqlite+aiosqlite:///./app.db"
```

3) Запусти приложение:
```bash
uvicorn app.main:app --reload
```
Документация будет доступна на `/docs` и `/redoc`.

## Конфигурация
Файл `app/core/config.py` читает переменные окружения из `.env`:
- `APP_TITLE` → заголовок приложения
- `APP_DESCRIPTION` → описание приложения
- `DATABASE_URL` → строка подключения SQLAlchemy (по умолчанию `sqlite+aiosqlite:///./app.db`)

## База данных и миграции
- По умолчанию используется SQLite (async, aiosqlite). Тесты создают отдельную БД `tests/test.db` и переопределяют сессию.
- Миграции (Alembic):
```bash
alembic revision -m "message" --autogenerate
alembic upgrade head
```

## Эндпоинты (основные)
- Проекты (`app/api/endpoints/charity_project.py`)
  - `GET /charity_project/` — список проектов
  - `POST /charity_project/` — только суперюзер, уникальное `name`, автоинвест из очереди донатов
  - `PATCH /charity_project/{id}` — только суперюзер; нельзя править закрытый; `full_amount` ≥ `invested_amount`
  - `DELETE /charity_project/{id}` — только суперюзер; нельзя удалить, если есть инвестиции/закрыт
- Пожертвования (`app/api/endpoints/donation.py`)
  - `POST /donation/` — для авторизованного пользователя; автоинвест в открытые проекты
  - `GET /donation/my` — пожертвования текущего пользователя
  - `GET /donation/` — только суперюзер, полный список
- Аутентификация (`app/api/endpoints/auth.py`)
  - `POST /auth/register` — регистрация (пароль ≥ 3 символов)
  - `POST /auth/login` — вход, возвращает JWT `{ access_token, token_type }`

## Аутентификация (JWT)
- Конфиг: `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `ALGORITHM` — см. `.env.example`.
- Как войти:
  1) `POST /auth/register` с `{"email", "password"}`
  2) `POST /auth/login` с теми же данными → получите `access_token`
  3) Используй заголовок: `Authorization: Bearer <access_token>`

## Инвестиционная логика
Реализована в `app/services/investment.py`:
- FIFO-распределение средств между открытыми проектами и донатами
- Автозакрытие сущности при достижении `invested_amount == full_amount` с установкой `close_date` (секундная точность)

## Тесты
```bash
pytest -q
```

## Заметки по разработке
- `app/core/user.py` содержит заглушки зависимостей `current_user` и `current_superuser`; в тестах они переопределяются фикстурами.
- Модели: `create_date` задаётся на стороне Python, чтобы отличались метки времени при быстрых операциях.

— С любовью и неоном, Кейт.