import pytest
from pydantic import ValidationError

from app.core.config import Settings


MANAGED_ENV_KEYS = [
    "APP_ENV",
    "SECRET_KEY",
    "ACTION_TOKEN_EXPOSE_IN_RESPONSE",
    "BILLING_ALLOW_MANUAL_PLAN_CHANGE",
    "STRIPE_ALLOW_INSECURE_WEBHOOKS",
    "RAILWAY_ENVIRONMENT_NAME",
    "LOG_LEVEL",
    "JSON_LOGS_ENABLED",
    "SENTRY_DSN",
    "SENTRY_TRACES_SAMPLE_RATE",
]


def _build_settings(monkeypatch, **env_values) -> Settings:
    for key in MANAGED_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    for key, value in env_values.items():
        monkeypatch.setenv(key, str(value))

    return Settings(_env_file=None)


def test_local_defaults_enable_only_local_dev_conveniences(monkeypatch):
    settings = _build_settings(
        monkeypatch,
        APP_ENV="local",
        SECRET_KEY="local-dev-secret",
    )

    assert settings.runtime.is_local is True
    assert settings.auth.action_token_expose_in_response is True
    assert settings.billing.allow_manual_plan_change is True
    assert settings.billing.allow_insecure_stripe_webhooks is False


def test_staging_defaults_are_safe_when_overrides_are_unset(monkeypatch):
    settings = _build_settings(
        monkeypatch,
        APP_ENV="staging",
        SECRET_KEY="staging-secret",
    )

    assert settings.runtime.is_staging is True
    assert settings.auth.action_token_expose_in_response is False
    assert settings.billing.allow_manual_plan_change is False
    assert settings.billing.allow_insecure_stripe_webhooks is False


def test_observability_settings_are_typed_and_grouped(monkeypatch):
    settings = _build_settings(
        monkeypatch,
        APP_ENV="production",
        SECRET_KEY="prod-secret",
        LOG_LEVEL="debug",
        JSON_LOGS_ENABLED="false",
        SENTRY_DSN="https://public@example.ingest.sentry.io/1",
        SENTRY_TRACES_SAMPLE_RATE="0.75",
    )

    assert settings.observability.log_level == "DEBUG"
    assert settings.observability.json_logs_enabled is False
    assert settings.observability.sentry_enabled is True
    assert settings.observability.sentry_traces_sample_rate == 0.75


def test_action_token_exposure_is_rejected_outside_local_or_test(monkeypatch):
    with pytest.raises(ValidationError):
        _build_settings(
            monkeypatch,
            APP_ENV="staging",
            SECRET_KEY="staging-secret",
            ACTION_TOKEN_EXPOSE_IN_RESPONSE="true",
        )


def test_manual_plan_changes_are_rejected_outside_local_or_test(monkeypatch):
    with pytest.raises(ValidationError):
        _build_settings(
            monkeypatch,
            APP_ENV="staging",
            SECRET_KEY="staging-secret",
            BILLING_ALLOW_MANUAL_PLAN_CHANGE="true",
        )


def test_insecure_stripe_webhooks_are_rejected_outside_local_or_test(monkeypatch):
    with pytest.raises(ValidationError):
        _build_settings(
            monkeypatch,
            APP_ENV="production",
            SECRET_KEY="prod-secret",
            STRIPE_ALLOW_INSECURE_WEBHOOKS="true",
        )


def test_railway_requires_explicit_non_local_environment(monkeypatch):
    with pytest.raises(ValidationError):
        _build_settings(
            monkeypatch,
            SECRET_KEY="railway-secret",
            RAILWAY_ENVIRONMENT_NAME="production",
        )
