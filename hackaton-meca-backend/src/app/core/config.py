from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator
from typing import List, Union

# correo
from pydantic import EmailStr


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    MEDIA_DIR: str = "./media"
    CORS_ORIGINS: List[str] = [
        "http://localhost:4200",
        "https://vercel-zoo-connect.vercel.app",
        "https://vercel-zoo-connect-git-main-mfjm0265-7988s-projects.vercel.app",
        "https://zoo-connect-completo.vercel.app",
    ]
    DEFAULT_ADMIN_EMAIL: str
    DEFAULT_ADMIN_PASSWORD: str
    DEFAULT_ADMIN_PHONE: str = "+10000000001"
    #
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    #
    # correo - Postmark (API HTTPS - compatible con Render)
    POSTMARK_SERVER_TOKEN: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_FROM: EmailStr
    MAIL_FROM_NAME: str = "ZooConnect"
    # 2fa
    TOTP_ENCRYPTION_KEY: str
    # redis
    REDIS_URL: str | None = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    # automatizacion tareas
    TIMEZONE: str = "America/La_Paz"

    @property
    def redis_connection_url(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    #
    FRONTEND_RESET_PASSWORD_URL: AnyHttpUrl = "http://localhost:3000/reset-password"
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # ReCAPTCHA v2 (Google) - Visible widget
    RECAPTCHA_SECRET_KEY: str
    RECAPTCHA_SITE_KEY: str = "6Lcxxxxxxxxxxxxxxxxxxxxxxxxx"
    RECAPTCHA_VERIFY_URL: str = "https://www.google.com/recaptcha/api/siteverify"
    REQUIRE_RECAPTCHA: bool = True
    TEXTBEE_API_BASE_URL: str = "https://api.textbee.dev/api/v1"
    TEXTBEE_API_KEY: str = ""
    TEXTBEE_DEVICE_ID: str = ""
    SMS_OTP_EXPIRE_MINUTES: int = 10
    #
    #
    # Políticas de histórico de contraseñas por rol
    PASSWORD_HISTORY_ADMIN_MAX: int = 5
    PASSWORD_HISTORY_ESPECIALISTA_MAX: int = 5  # veterinario, cuidador
    PASSWORD_HISTORY_PACIENTE_MAX: int = 3  # visitante
    PASSWORD_HISTORY_USUARIO_BASICO_MAX: int = 3
    #
    # Días de validez de contraseña por rol
    PASSWORD_VALIDITY_ADMIN_DAYS: int = 90
    PASSWORD_VALIDITY_ESPECIALISTA_DAYS: int = 90
    PASSWORD_VALIDITY_PACIENTE_DAYS: int = 180
    PASSWORD_VALIDITY_USUARIO_BASICO_DAYS: int = 180
    #

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str):
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    import json
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v


settings = Settings()
