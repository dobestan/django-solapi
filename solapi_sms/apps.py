from django.apps import AppConfig


class SolapiSmsConfig(AppConfig):
    """Django app configuration for SOLAPI SMS."""

    name = "solapi_sms"
    verbose_name = "SOLAPI SMS"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import signals  # noqa: F401
