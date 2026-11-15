"""Settings from the environment (AD-14): Mock mode by default, start-up guards outside local."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

from config import env as cfg

ROOT = Path(__file__).resolve().parent.parent

SAFE_PRODUCTION = {
    "APP_ENV": "production",
    "SECRET_KEY": "a-long-random-production-secret",
    "DEBUG": "false",
    "ALLOWED_HOSTS": "study.example.org",
    "CSRF_TRUSTED_ORIGINS": "https://study.example.org",
}


def env_example_names():
    lines = (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
    return [line.split("=", 1)[0] for line in lines if "=" in line and not line.startswith("#")]


def run_django(tmp_path, extra_env, *args):
    """Start Django in a clean process with only the given settings.

    Every variable in .env.example is set explicitly (empty by default), so neither the
    developer's shell nor the repository's .env can leak in: load_dotenv never overrides.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_")}
    env.update({name: "" for name in env_example_names()})
    env.update({"APP_ENV": "local", "DATA_DIR": str(tmp_path / "data")})
    env.update(extra_env)
    return subprocess.run(
        [sys.executable, "manage.py", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def shell_value(tmp_path, extra_env, expression, *options):
    code = f"from django.conf import settings; from django.db import connection; print({expression})"
    result = run_django(tmp_path, extra_env, "shell", "--no-imports", *options, "-c", code)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


# Effective AI provider (FR-20, AD-2)


def test_fr20_no_key_means_mock():
    assert cfg.effective_ai_provider({}) == "mock"
    assert cfg.effective_ai_provider({"AI_PROVIDER": "anthropic"}) == "mock"


def test_fr21_key_set_means_anthropic():
    assert cfg.effective_ai_provider({"ANTHROPIC_API_KEY": "x"}) == "anthropic"


def test_fr20_ai_provider_mock_forces_mock_with_key():
    assert cfg.effective_ai_provider({"ANTHROPIC_API_KEY": "x", "AI_PROVIDER": "mock"}) == "mock"


@pytest.mark.parametrize("env", [{"AI_PROVIDER": "antropic"}, {"ANTHROPIC_API_KEY": "x", "AI_PROVIDER": "gemini"}])
def test_unknown_ai_provider_is_refused_with_or_without_key(env):
    with pytest.raises(ImproperlyConfigured):
        cfg.effective_ai_provider(env)


def test_tests_always_run_in_mock_mode(settings):
    assert settings.AI_PROVIDER == "mock"


def test_ad15_test_settings_force_mock_even_with_a_key(tmp_path):
    value = shell_value(
        tmp_path, {"ANTHROPIC_API_KEY": "sk-ant-x"}, "settings.AI_PROVIDER", "--settings=config.settings_test"
    )
    assert value == "mock"


# Fresh clone (NFR-2)


def test_nfr2_fresh_clone_migrates_into_data_dir_in_mock_mode(tmp_path):
    result = run_django(tmp_path, {}, "migrate", "--no-input")
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "data" / "db.sqlite3").is_file()
    assert shell_value(tmp_path, {}, "settings.AI_PROVIDER") == "mock"
    assert shell_value(tmp_path, {}, "settings.DEBUG") == "True"


def test_invalid_boolean_is_refused():
    with pytest.raises(ImproperlyConfigured):
        cfg.get_bool({"DEBUG": "flase"}, "DEBUG", default=True)


def test_list_splits_commas_and_drops_blanks():
    assert cfg.get_list({"HOSTS": "a.no, b.no,,"}, "HOSTS", []) == ["a.no", "b.no"]


def test_empty_app_env_counts_as_local():
    assert cfg.is_local({"APP_ENV": " "}) is True
    assert cfg.is_local({"APP_ENV": "production"}) is False


def test_copied_env_example_with_empty_values_keeps_local_defaults():
    assert cfg.get_bool({"DEBUG": ""}, "DEBUG", default=True) is True
    assert cfg.get_list({"ALLOWED_HOSTS": " "}, "ALLOWED_HOSTS", ["localhost"]) == ["localhost"]


def test_key_is_not_in_settings_output(tmp_path):
    result = run_django(tmp_path, {"ANTHROPIC_API_KEY": "sk-ant-secret-value"}, "check")
    assert result.returncode == 0, result.stderr
    assert "sk-ant-secret-value" not in result.stdout + result.stderr


def test_sqlite_options(settings):
    options = settings.DATABASES["default"]["OPTIONS"]
    assert options["transaction_mode"] == "IMMEDIATE"
    assert options["timeout"] >= 5
    assert "journal_mode=WAL" in options["init_command"]
    assert settings.ATOMIC_REQUESTS is False


def test_ad19_sqlite_runs_in_wal_mode(tmp_path):
    assert run_django(tmp_path, {}, "migrate", "--no-input").returncode == 0
    mode = shell_value(tmp_path, {}, "connection.cursor().execute('PRAGMA journal_mode').fetchone()[0]")
    sync = shell_value(tmp_path, {}, "connection.cursor().execute('PRAGMA synchronous').fetchone()[0]")
    assert mode == "wal"
    assert sync == "1"  # NORMAL


def test_time_settings(settings):
    assert settings.USE_TZ is True
    assert settings.TIME_ZONE == "Europe/Oslo"


# Start-up guards outside local (AD-14)


def test_unsafe_production_refuses_to_start_naming_secret_key(tmp_path):
    env = dict(SAFE_PRODUCTION, SECRET_KEY="")
    result = run_django(tmp_path, env, "check")
    assert result.returncode != 0
    assert "SECRET_KEY" in result.stderr


@pytest.mark.parametrize(
    ("override", "named"),
    [
        ({"DEBUG": "true"}, "DEBUG"),
        ({"ALLOWED_HOSTS": ""}, "ALLOWED_HOSTS"),
        ({"CSRF_TRUSTED_ORIGINS": ""}, "CSRF_TRUSTED_ORIGINS"),
    ],
)
def test_each_production_guard_is_named(tmp_path, override, named):
    result = run_django(tmp_path, dict(SAFE_PRODUCTION, **override), "check")
    assert result.returncode != 0
    assert named in result.stderr


def test_safe_production_starts(tmp_path):
    result = run_django(tmp_path, SAFE_PRODUCTION, "check")
    assert result.returncode == 0, result.stderr
    assert shell_value(tmp_path, SAFE_PRODUCTION, "settings.SESSION_COOKIE_SECURE") == "True"
    assert shell_value(tmp_path, SAFE_PRODUCTION, "settings.CSRF_COOKIE_SECURE") == "True"


def test_production_debug_defaults_to_off_when_empty(tmp_path):
    env = dict(SAFE_PRODUCTION, DEBUG="")
    assert run_django(tmp_path, env, "check").returncode == 0
    assert shell_value(tmp_path, env, "settings.DEBUG") == "False"


def test_production_problems_cover_cookies_and_admin():
    problems = cfg.production_problems(
        secret_key="real",
        debug=False,
        allowed_hosts_set=True,
        csrf_trusted_origins_set=True,
        session_cookie_secure=False,
        csrf_cookie_secure=False,
        installed_apps=["django.contrib.admin"],
    )
    assert any("SESSION_COOKIE_SECURE" in p for p in problems)
    assert any("CSRF_COOKIE_SECURE" in p for p in problems)
    assert any("admin" in p for p in problems)


def test_admin_is_not_installed(settings):
    assert "django.contrib.admin" not in settings.INSTALLED_APPS
