from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "cloudy.accounts"

    def ready(self):
        from django.contrib.auth.models import User

        if not hasattr(User, "get_profile"):
            User.add_to_class("get_profile", property(lambda self: self.userprofile))
