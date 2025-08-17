from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_title: str = Field(
        'Пожертвования на благотворительный фонд QRKot', env='APP_TITLE'
    )
    app_description: str = Field(
        'API сервиса благотворительного фонда QRKot', env='APP_DESCRIPTION'
    )
    # Default async SQLite URL to satisfy tests and local runs
    database_url: str = Field(
        'sqlite+aiosqlite:///./app.db',
        env='DATABASE_URL'
    )

    # Auth settings
    secret_key: str = Field('insecure-dev-secret', env='SECRET_KEY')
    access_token_expire_minutes: int = Field(
        60 * 24,
        env='ACCESS_TOKEN_EXPIRE_MINUTES'
    )
    algorithm: str = Field('HS256', env='ALGORITHM')

    class Config:
        env_file = '.env'


settings = Settings()