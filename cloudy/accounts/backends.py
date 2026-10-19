from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class EmailBackend(ModelBackend):
    """Authenticate with the email address users actually type on the login form.

    Production usernames are generated slugs (e.g. ``PILOT-abcde``), not emails.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get("email") or username
        if email is None or password is None:
            return None

        users = User.objects.filter(email__iexact=email).order_by("-last_login", "-pk")
        if not users.exists():
            User().set_password(password)
            return None

        for user in users:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
