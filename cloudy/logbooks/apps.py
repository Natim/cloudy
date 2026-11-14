from django.apps import AppConfig


class LogbooksConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "cloudy.logbooks"

    def ready(self):
        # Receivers are registered at import time. Nothing else imports this module.
        from cloudy.logbooks import signals  # noqa: F401
