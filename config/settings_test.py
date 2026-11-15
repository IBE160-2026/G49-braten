"""Settings for the test run: always Mock mode, even when .env holds a Key (AD-2, AD-15)."""

from config.settings import *  # noqa: F403

AI_PROVIDER = "mock"

# A test-only app with an owned model, so core.ownership is tested without a feature model.
INSTALLED_APPS = [*INSTALLED_APPS, "tests.ownership_app"]  # noqa: F405
