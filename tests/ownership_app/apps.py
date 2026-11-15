from django.apps import AppConfig


class OwnershipAppConfig(AppConfig):
    """Test-only app; it has no migrations, so the test database creates its table directly."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.ownership_app"
    label = "ownership_app"
