from __future__ import annotations

import contextvars
from datetime import datetime, timedelta, UTC

import jwt
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpRequest
from ninja.errors import HttpError
from ninja.security import HttpBearer

_api_user: contextvars.ContextVar[User | None] = contextvars.ContextVar("api_user", default=None)

JWT_ALGORITHM = "HS256"


def set_api_user(user: User | None) -> None:
    _api_user.set(user)


def get_api_user() -> User | None:
    return _api_user.get()


def issue_access_token(user: User) -> tuple[str, int]:
    expires_in = settings.API_JWT_EXPIRY_SECONDS
    now = datetime.now(tz=UTC)
    payload = {
        "user_id": user.pk,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)
    if isinstance(token, bytes):
        token = token.decode()
    return token, expires_in


def user_from_access_token(token: str) -> User | None:
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "iat", "user_id"]},
        )
    except jwt.PyJWTError:
        return None
    try:
        user_id = int(payload["user_id"])
    except KeyError, TypeError, ValueError:
        return None
    user = User.objects.filter(pk=user_id, is_active=True).first()
    return user


def authenticate_bearer(request: HttpRequest) -> User | None:
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("Bearer "):
        return None
    return user_from_access_token(auth[7:].strip())


class JwtBearer(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str) -> User | None:
        user = user_from_access_token(token)
        if user is None:
            return None
        set_api_user(user)
        return user


def require_user(request: HttpRequest) -> User:
    user = getattr(request, "auth", None)
    if user is None:
        raise HttpError(401, "Invalid or missing bearer token")
    return user
