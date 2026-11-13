from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "cloudy.core"

    def ready(self):
        # Connect the signal receivers declared in tasks.py (storage usage per user).
        from . import tasks
