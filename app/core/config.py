from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Vee API"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vee"

    # Firebase Authentication
    # Required for all authenticated endpoints.
    # Obtain from Firebase Console → Project Settings → Service Accounts.
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_PRIVATE_KEY: str = ""  # Full PEM key; \\n is normalized automatically.

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
