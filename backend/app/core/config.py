from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "StudyOS API"
    app_version: str = "0.1.0"
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/studyos"
    secret_key: str = "change-this-in-production"
    access_token_expire_minutes: int = 60 * 24
    refresh_token_expire_minutes: int = 60 * 24 * 30
    algorithm: str = "HS256"
    cors_origins: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173,"
        "https://study-os-xi.vercel.app,"
        "https://studyos-staging.vercel.app"
    )
    login_rate_limit: int = 10
    login_rate_window_seconds: int = 300
    email_verification_token_expire_minutes: int = 60
    password_reset_token_expire_minutes: int = 30
    action_token_expose_in_response: bool = True
    public_app_url: str = "http://localhost:5173"
    email_provider: str = "console"
    email_from: str = "noreply@studyos.dev"
    email_smtp_host: str = "localhost"
    email_smtp_port: int = 587
    email_smtp_username: str = ""
    email_smtp_password: str = ""
    email_smtp_use_tls: bool = True
    email_resend_api_key: str = ""
    email_resend_base_url: str = "https://api.resend.com/emails"
    email_max_attempts: int = 5
    email_worker_poll_seconds: int = 5
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 0.2

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
