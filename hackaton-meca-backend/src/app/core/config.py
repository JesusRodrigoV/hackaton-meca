import json
from pathlib import Path
from typing import List, Literal, Union

from pydantic import EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    TIMEZONE: str = "America/La_Paz"

    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    CHANGE_PASSWORD_TOKEN_EXPIRE_MINUTES: int = 10
    TWO_FACTOR_SESSION_EXPIRE_MINUTES: int = 5
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # Refresh cookie
    REFRESH_COOKIE_NAME: str = "meca_refresh_token"
    REFRESH_COOKIE_SECURE: bool | None = None
    REFRESH_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    REFRESH_COOKIE_PATH: str = "/api/v1/auth"

    # 2FA / TOTP
    TOTP_ISSUER: str = "MECA"
    TOTP_ENCRYPTION_KEY: str
    BACKUP_CODE_COUNT: int = 5

    # Login lockout
    MAX_FAILED_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 5

    # Email (SMTP only)
    MAIL_ENABLED: bool = True
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_SERVER: str = ""
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_FROM: EmailStr = "no-reply@meca.local"
    MAIL_FROM_NAME: str = "MECA"
    FRONTEND_RESET_PASSWORD_URL: str = "http://localhost:3000/reset-password"

    # CORS
    CORS_ORIGINS: List[str] = []

    # Redis (optional rate limiting / cache)
    REDIS_URL: str | None = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Files
    MEDIA_DIR: str = "./media"
    REPORTS_DIR: str = "./media/reports"

    @property
    def refresh_cookie_secure(self) -> bool:
        if self.REFRESH_COOKIE_SECURE is not None:
            return self.REFRESH_COOKIE_SECURE
        return self.ENVIRONMENT.lower() == "production"

    @property
    def redis_connection_url(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, value: str) -> str:
        if value and value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql://", 1)
        return value

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, value: Union[str, List[str]]):
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                try:
                    return json.loads(stripped)
                except json.JSONDecodeError:
                    pass
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value


settings = Settings()