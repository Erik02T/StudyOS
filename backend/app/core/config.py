import logging
from enum import Enum
from functools import cached_property, lru_cache

from pydantic import BaseModel, Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "d002c9b-8f1e-4c3a-9c3b-2f0e5d6a7b8c"
DEFAULT_PUBLIC_APP_URL = "http://127.0.0.1:3000"
DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://study-os-xi.vercel.app",
    "https://studyos-staging.vercel.app",
)
DEFAULT_DATABASE_URL = "postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/studyos"
logger = logging.getLogger("studyos.config")
_last_logged_settings_validation_summary: str | None = None


class RuntimeEnvironment(str, Enum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class RuntimeSettings(BaseModel):
    environment: RuntimeEnvironment
    railway_environment_name: str | None = None
    running_in_ci: bool = False

    @property
    def is_local(self) -> bool:
        return self.environment == RuntimeEnvironment.LOCAL

    @property
    def is_test(self) -> bool:
        return self.environment == RuntimeEnvironment.TEST

    @property
    def is_staging(self) -> bool:
        return self.environment == RuntimeEnvironment.STAGING

    @property
    def is_production(self) -> bool:
        return self.environment == RuntimeEnvironment.PRODUCTION

    @property
    def is_local_like(self) -> bool:
        return self.environment in {RuntimeEnvironment.LOCAL, RuntimeEnvironment.TEST}

    @property
    def is_deployed(self) -> bool:
        return bool(self.railway_environment_name)


class AppSettings(BaseModel):
    name: str
    version: str
    public_app_url: str
    cors_origins: tuple[str, ...]
    cors_allow_origin_regex: str | None = None
    security_headers_enabled: bool = True


class DatabaseSettings(BaseModel):
    url: str


class AuthSettings(BaseModel):
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_minutes: int
    login_rate_limit: int
    login_rate_window_seconds: int
    email_verification_token_expire_minutes: int
    password_reset_token_expire_minutes: int
    action_token_expose_in_response: bool


class EmailSettings(BaseModel):
    provider: str
    from_address: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool
    resend_api_key: str
    resend_base_url: str
    max_attempts: int
    worker_poll_seconds: int


class BillingPlanLimits(BaseModel):
    max_subjects: int
    tasks_per_month: int
    reviews_per_month: int
    sessions_per_month: int


class BillingSettings(BaseModel):
    allow_manual_plan_change: bool
    free_limits: BillingPlanLimits
    pro_limits: BillingPlanLimits
    stripe_secret_key: str
    stripe_webhook_secret: str
    stripe_price_pro_monthly: str
    allow_insecure_stripe_webhooks: bool


class ObservabilitySettings(BaseModel):
    log_level: str
    json_logs_enabled: bool
    sentry_dsn: str
    sentry_traces_sample_rate: float

    @property
    def sentry_enabled(self) -> bool:
        return bool(self.sentry_dsn)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment / runtime
    environment: RuntimeEnvironment = Field(default=RuntimeEnvironment.LOCAL, validation_alias="APP_ENV")
    railway_environment_name: str = Field(default="", validation_alias="RAILWAY_ENVIRONMENT_NAME")
    running_in_ci: bool = Field(default=False, validation_alias="CI")

    # App
    app_name: str = Field(default="StudyOS API", validation_alias="APP_NAME")
    app_version: str = Field(default="0.1.0", validation_alias="APP_VERSION")
    public_app_url: str = Field(default=DEFAULT_PUBLIC_APP_URL, validation_alias="PUBLIC_APP_URL")
    cors_origins: str = Field(
        default=",".join(DEFAULT_CORS_ORIGINS),
        validation_alias="CORS_ORIGINS",
    )
    cors_allow_origin_regex: str = Field(default=r"^https:\/\/.*\.vercel\.app$", validation_alias="CORS_ALLOW_ORIGIN_REGEX")
    security_headers_enabled: bool = Field(default=True, validation_alias="SECURITY_HEADERS_ENABLED")

    # Database
    database_url: str = Field(
        default=DEFAULT_DATABASE_URL,
        validation_alias="DATABASE_URL",
    )

    # Auth
    secret_key: str = Field(default=DEFAULT_SECRET_KEY, validation_alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=60 * 24, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_minutes: int = Field(default=60 * 24 * 30, validation_alias="REFRESH_TOKEN_EXPIRE_MINUTES")
    algorithm: str = Field(default="HS256", validation_alias="ALGORITHM")
    login_rate_limit: int = Field(default=10, validation_alias="LOGIN_RATE_LIMIT")
    login_rate_window_seconds: int = Field(default=300, validation_alias="LOGIN_RATE_WINDOW_SECONDS")
    email_verification_token_expire_minutes: int = Field(
        default=60,
        validation_alias="EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES",
    )
    password_reset_token_expire_minutes: int = Field(
        default=30,
        validation_alias="PASSWORD_RESET_TOKEN_EXPIRE_MINUTES",
    )
    action_token_expose_in_response_override: bool | None = Field(
        default=None,
        validation_alias="ACTION_TOKEN_EXPOSE_IN_RESPONSE",
    )

    # Email
    email_provider: str = Field(default="console", validation_alias="EMAIL_PROVIDER")
    email_from: str = Field(default="noreply@studyos.dev", validation_alias="EMAIL_FROM")
    email_smtp_host: str = Field(default="localhost", validation_alias="EMAIL_SMTP_HOST")
    email_smtp_port: int = Field(default=587, validation_alias="EMAIL_SMTP_PORT")
    email_smtp_username: str = Field(default="", validation_alias="EMAIL_SMTP_USERNAME")
    email_smtp_password: str = Field(default="", validation_alias="EMAIL_SMTP_PASSWORD")
    email_smtp_use_tls: bool = Field(default=True, validation_alias="EMAIL_SMTP_USE_TLS")
    email_resend_api_key: str = Field(default="", validation_alias="EMAIL_RESEND_API_KEY")
    email_resend_base_url: str = Field(
        default="https://api.resend.com/emails",
        validation_alias="EMAIL_RESEND_BASE_URL",
    )
    email_max_attempts: int = Field(default=5, validation_alias="EMAIL_MAX_ATTEMPTS")
    email_worker_poll_seconds: int = Field(default=5, validation_alias="EMAIL_WORKER_POLL_SECONDS")

    # Billing
    billing_allow_manual_plan_change_override: bool | None = Field(
        default=None,
        validation_alias="BILLING_ALLOW_MANUAL_PLAN_CHANGE",
    )
    billing_free_max_subjects: int = Field(default=10, validation_alias="BILLING_FREE_MAX_SUBJECTS")
    billing_free_tasks_per_month: int = Field(default=150, validation_alias="BILLING_FREE_TASKS_PER_MONTH")
    billing_free_reviews_per_month: int = Field(default=600, validation_alias="BILLING_FREE_REVIEWS_PER_MONTH")
    billing_free_sessions_per_month: int = Field(default=200, validation_alias="BILLING_FREE_SESSIONS_PER_MONTH")
    billing_pro_max_subjects: int = Field(default=999999, validation_alias="BILLING_PRO_MAX_SUBJECTS")
    billing_pro_tasks_per_month: int = Field(default=999999, validation_alias="BILLING_PRO_TASKS_PER_MONTH")
    billing_pro_reviews_per_month: int = Field(default=999999, validation_alias="BILLING_PRO_REVIEWS_PER_MONTH")
    billing_pro_sessions_per_month: int = Field(default=999999, validation_alias="BILLING_PRO_SESSIONS_PER_MONTH")
    stripe_secret_key: str = Field(default="", validation_alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(default="", validation_alias="STRIPE_WEBHOOK_SECRET")
    stripe_price_pro_monthly: str = Field(default="", validation_alias="STRIPE_PRICE_PRO_MONTHLY")
    stripe_allow_insecure_webhooks_override: bool | None = Field(
        default=None,
        validation_alias="STRIPE_ALLOW_INSECURE_WEBHOOKS",
    )

    # Observability
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    json_logs_enabled: bool = Field(default=True, validation_alias="JSON_LOGS_ENABLED")
    sentry_dsn: str = Field(default="", validation_alias="SENTRY_DSN")
    sentry_traces_sample_rate: float = Field(default=0.2, validation_alias="SENTRY_TRACES_SAMPLE_RATE")

    @staticmethod
    def _split_csv(value: str) -> tuple[str, ...]:
        return tuple(item.strip() for item in value.split(",") if item.strip())

    def _resolve_local_only_override(self, override: bool | None, *, local_default: bool) -> bool:
        if override is not None:
            return override
        return self.environment == RuntimeEnvironment.LOCAL and local_default

    @property
    def action_token_expose_in_response(self) -> bool:
        return self._resolve_local_only_override(
            self.action_token_expose_in_response_override,
            local_default=True,
        )

    @property
    def billing_allow_manual_plan_change(self) -> bool:
        return self._resolve_local_only_override(
            self.billing_allow_manual_plan_change_override,
            local_default=True,
        )

    @property
    def stripe_allow_insecure_webhooks(self) -> bool:
        return self._resolve_local_only_override(
            self.stripe_allow_insecure_webhooks_override,
            local_default=False,
        )

    @model_validator(mode="after")
    def validate_runtime_safety(self) -> "Settings":
        if self.secret_key == DEFAULT_SECRET_KEY and self.environment in {
            RuntimeEnvironment.STAGING,
            RuntimeEnvironment.PRODUCTION,
        }:
            raise ValueError("SECRET_KEY must be set explicitly for staging and production environments")

        if self.action_token_expose_in_response and self.environment not in {
            RuntimeEnvironment.LOCAL,
            RuntimeEnvironment.TEST,
        }:
            raise ValueError("ACTION_TOKEN_EXPOSE_IN_RESPONSE is only allowed for local/test usage")

        if self.billing_allow_manual_plan_change and self.environment not in {
            RuntimeEnvironment.LOCAL,
            RuntimeEnvironment.TEST,
        }:
            raise ValueError("BILLING_ALLOW_MANUAL_PLAN_CHANGE is only allowed for local/test usage")

        if self.stripe_allow_insecure_webhooks and self.environment not in {
            RuntimeEnvironment.LOCAL,
            RuntimeEnvironment.TEST,
        }:
            raise ValueError("STRIPE_ALLOW_INSECURE_WEBHOOKS is only allowed for local/test usage")

        if self.railway_environment_name and self.environment == RuntimeEnvironment.LOCAL:
            raise ValueError("APP_ENV must be explicitly set when running on Railway")

        return self

    @cached_property
    def runtime(self) -> RuntimeSettings:
        return RuntimeSettings(
            environment=self.environment,
            railway_environment_name=self.railway_environment_name or None,
            running_in_ci=self.running_in_ci,
        )

    @cached_property
    def app(self) -> AppSettings:
        return AppSettings(
            name=self.app_name,
            version=self.app_version,
            public_app_url=self.public_app_url,
            cors_origins=self._split_csv(self.cors_origins),
            cors_allow_origin_regex=self.cors_allow_origin_regex or None,
            security_headers_enabled=self.security_headers_enabled,
        )

    @cached_property
    def database(self) -> DatabaseSettings:
        return DatabaseSettings(url=self.database_url)

    @cached_property
    def auth(self) -> AuthSettings:
        return AuthSettings(
            secret_key=self.secret_key,
            algorithm=self.algorithm,
            access_token_expire_minutes=self.access_token_expire_minutes,
            refresh_token_expire_minutes=self.refresh_token_expire_minutes,
            login_rate_limit=self.login_rate_limit,
            login_rate_window_seconds=self.login_rate_window_seconds,
            email_verification_token_expire_minutes=self.email_verification_token_expire_minutes,
            password_reset_token_expire_minutes=self.password_reset_token_expire_minutes,
            action_token_expose_in_response=self.action_token_expose_in_response,
        )

    @cached_property
    def email(self) -> EmailSettings:
        return EmailSettings(
            provider=self.email_provider,
            from_address=self.email_from,
            smtp_host=self.email_smtp_host,
            smtp_port=self.email_smtp_port,
            smtp_username=self.email_smtp_username,
            smtp_password=self.email_smtp_password,
            smtp_use_tls=self.email_smtp_use_tls,
            resend_api_key=self.email_resend_api_key,
            resend_base_url=self.email_resend_base_url,
            max_attempts=self.email_max_attempts,
            worker_poll_seconds=self.email_worker_poll_seconds,
        )

    @cached_property
    def billing(self) -> BillingSettings:
        return BillingSettings(
            allow_manual_plan_change=self.billing_allow_manual_plan_change,
            free_limits=BillingPlanLimits(
                max_subjects=self.billing_free_max_subjects,
                tasks_per_month=self.billing_free_tasks_per_month,
                reviews_per_month=self.billing_free_reviews_per_month,
                sessions_per_month=self.billing_free_sessions_per_month,
            ),
            pro_limits=BillingPlanLimits(
                max_subjects=self.billing_pro_max_subjects,
                tasks_per_month=self.billing_pro_tasks_per_month,
                reviews_per_month=self.billing_pro_reviews_per_month,
                sessions_per_month=self.billing_pro_sessions_per_month,
            ),
            stripe_secret_key=self.stripe_secret_key,
            stripe_webhook_secret=self.stripe_webhook_secret,
            stripe_price_pro_monthly=self.stripe_price_pro_monthly,
            allow_insecure_stripe_webhooks=self.stripe_allow_insecure_webhooks,
        )

    @cached_property
    def observability(self) -> ObservabilitySettings:
        return ObservabilitySettings(
            log_level=self.log_level.upper(),
            json_logs_enabled=self.json_logs_enabled,
            sentry_dsn=self.sentry_dsn,
            sentry_traces_sample_rate=self.sentry_traces_sample_rate,
        )


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        _log_settings_validation_error(exc)
        raise


def _log_settings_validation_error(exc: ValidationError) -> None:
    global _last_logged_settings_validation_summary

    summary = _summarize_settings_validation_error(exc)
    if summary == _last_logged_settings_validation_summary:
        return

    _last_logged_settings_validation_summary = summary
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.ERROR, format="%(message)s")
    logger.error(summary)


def _summarize_settings_validation_error(exc: ValidationError) -> str:
    lines = ["Settings validation failed during startup. Fix the environment configuration and restart."]
    for error in exc.errors(include_url=False):
        location = _format_settings_error_location(error.get("loc", ()))
        message = error.get("msg", "Invalid value")
        lines.append(f"- {location}: {message}")
    return "\n".join(lines)


def _format_settings_error_location(loc: tuple[object, ...] | list[object]) -> str:
    if not loc:
        return "settings"

    alias_to_field_name = {
        str(field.validation_alias): field_name
        for field_name, field in Settings.model_fields.items()
        if field.validation_alias is not None
    }
    normalized_parts = []
    for part in loc:
        if isinstance(part, str):
            normalized_parts.append(alias_to_field_name.get(part, part))
        else:
            normalized_parts.append(str(part))
    return ".".join(normalized_parts)
