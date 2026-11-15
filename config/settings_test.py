"""Settings for the test run: always Mock mode, even when .env holds a Key (AD-2, AD-15)."""

from config.settings import *  # noqa: F403

AI_PROVIDER = "mock"
