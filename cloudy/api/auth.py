from __future__ import annotations

import contextvars

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import HttpRequest
from ninja.errors import HttpError
from ninja.security import HttpBearer

from cloudy.accounts.models import UserProfile

_api_user: contextvars.ContextVar[User | None] = contextvars.ContextVar("api_user", default=None)


def set_api_user(user: User | None) -> None:
    _api_user.set(user)


def get_api_user() -> User | None:
    return _api_user.get()


def user_from_api_key(api_key: str) -> User | None:
    if not api_key:
        return None
    profile = UserProfile.objects.filter(api_key=api_key).select_related("user").first()
    if profile is None or not profile.user.is_active:
        return None
    return profile.user


def authenticate_bearer(request: HttpRequest) -> User | None:
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("Bearer "):
        return None
    return user_from_api_key(auth[7:].strip())


class ApiKeyBearer(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str) -> User | None:
        user = user_from_api_key(token)
        if user is None:
            return None
        set_api_user(user)
        return user


def require_user(request: HttpRequest) -> User:
    user = getattr(request, "auth", None)
    if user is None:
        raise HttpError(401, "Invalid or missing API key")
    return user


def exchange_email_password(email: str, password: str) -> str:
    user = authenticate(request=None, username=email, password=password)
    if user is None:
        raise HttpError(401, "Invalid credentials")
    profile = user.userprofile
    if not profile.api_key:
        profile.generate_api_key()
    return profile.api_key
