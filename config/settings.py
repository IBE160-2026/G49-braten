"""Django settings for AI Study Buddy. Every setting comes from the environment (AD-14)."""

import os
from pathlib import Path

from dotenv import load_dotenv

from config.env import (
    DEV_SECRET_KEY,
    effective_ai_provider,
    get_bool,
    get_list,
    guard_production,
    is_local,
    production_problems,
)

BASE_DIR = Path(__file__).resolve().parent.parent

# Values already in the process environment win over .env.
load_dotenv(BASE_DIR / ".env", override=False)
env = os.environ

LOCAL = is_local(env)

SECRET_KEY = env.get("SECRET_KEY", "").strip() or DEV_SECRET_KEY
DEBUG = get_bool(env, "DEBUG", default=LOCAL)

ALLOWED_HOSTS = get_list(env, "ALLOWED_HOSTS", ["localhost", "127.0.0.1"] if LOCAL else [])
CSRF_TRUSTED_ORIGINS = get_list(env, "CSRF_TRUSTED_ORIGINS", [])

SESSION_COOKIE_SECURE = not LOCAL
CSRF_COOKIE_SECURE = not LOCAL

# The AI provider (AD-2). The Key is read here and never logged or rendered.
ANTHROPIC_API_KEY = env.get("ANTHROPIC_API_KEY", "").strip()
AI_PROVIDER = effective_ai_provider(env)

SIGNUP_ALLOWED_EMAILS = [e.lower() for e in get_list(env, "SIGNUP_ALLOWED_EMAILS", [])]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "core",
    "accounts",
    "courses",
    "ai",
    "ingestion",
    "studymat",
    "quiz",
    "review",
    "progress",
    "web",
]

if not LOCAL:
    guard_production(
        production_problems(
            secret_key=SECRET_KEY,
            debug=DEBUG,
            allowed_hosts_set=bool(ALLOWED_HOSTS),
            csrf_trusted_origins_set=bool(CSRF_TRUSTED_ORIGINS),
            session_cookie_secure=SESSION_COOKIE_SECURE,
            csrf_cookie_secure=CSRF_COOKIE_SECURE,
            installed_apps=INSTALLED_APPS,
        )
    )

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Data: one SQLite file in DATA_DIR (AD-16), created on start. WAL, IMMEDIATE, busy timeout (AD-19).
DATA_DIR = Path(env.get("DATA_DIR", "").strip() or BASE_DIR / "data").expanduser()
if not DATA_DIR.is_absolute():
    DATA_DIR = BASE_DIR / DATA_DIR
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db.sqlite3",
        "OPTIONS": {
            "transaction_mode": "IMMEDIATE",
            "timeout": 5,
            "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;",
        },
    }
}
ATOMIC_REQUESTS = False

AUTH_USER_MODEL = "accounts.Student"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

LANGUAGE_CODE = "nb"
TIME_ZONE = "Europe/Oslo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").is_dir() else []

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
