"""Reading settings from the environment (AD-14).

Pure functions over a mapping, so the rules can be tested without reloading settings.
"""

from collections.abc import Mapping

from django.core.exceptions import ImproperlyConfigured

DEV_SECRET_KEY = "dev-insecure-change-me-only-for-local-use"

TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}


def get_bool(env: Mapping[str, str], name: str, default: bool) -> bool:
    """An unset or empty variable gives the default, so a copied .env.example works."""
    raw = env.get(name)
    if raw is None or not raw.strip():
        return default
    value = raw.strip().lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise ImproperlyConfigured(f"{name} must be true or false, got {raw!r}.")


def get_list(env: Mapping[str, str], name: str, default: list[str]) -> list[str]:
    raw = env.get(name)
    if raw is None or not raw.strip():
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def is_local(env: Mapping[str, str]) -> bool:
    return env.get("APP_ENV", "local").strip().lower() in ("", "local")


def effective_ai_provider(env: Mapping[str, str]) -> str:
    """No Key means Mock, always (FR-20). AI_PROVIDER=mock forces Mock even with a Key."""
    requested = env.get("AI_PROVIDER", "").strip().lower()
    if requested not in ("", "mock", "anthropic"):
        raise ImproperlyConfigured(f"AI_PROVIDER must be 'mock' or 'anthropic', got {requested!r}.")
    if requested == "mock" or not env.get("ANTHROPIC_API_KEY", "").strip():
        return "mock"
    return "anthropic"


def production_problems(
    *,
    secret_key: str,
    debug: bool,
    allowed_hosts_set: bool,
    csrf_trusted_origins_set: bool,
    session_cookie_secure: bool,
    csrf_cookie_secure: bool,
    installed_apps: list[str],
) -> list[str]:
    """Every unmet start-up guard for a non-local environment, named by setting."""
    problems = []
    if not secret_key or secret_key == DEV_SECRET_KEY:
        problems.append("SECRET_KEY must be set to a non-default value")
    if debug:
        problems.append("DEBUG must be false")
    if not allowed_hosts_set:
        problems.append("ALLOWED_HOSTS must be set")
    if not csrf_trusted_origins_set:
        problems.append("CSRF_TRUSTED_ORIGINS must be set")
    if not session_cookie_secure:
        problems.append("SESSION_COOKIE_SECURE must be on")
    if not csrf_cookie_secure:
        problems.append("CSRF_COOKIE_SECURE must be on")
    if "django.contrib.admin" in installed_apps:
        problems.append("the admin must be disabled")
    return problems


def guard_production(problems: list[str]) -> None:
    if problems:
        raise ImproperlyConfigured(
            "Refusing to start outside APP_ENV=local: " + "; ".join(problems) + "."
        )
