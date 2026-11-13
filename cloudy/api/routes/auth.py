from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError

from cloudy.accounts.models import UserProfile

from ..auth import require_user, token_response
from ..schemas.auth import ProfileOut, TokenIn, TokenOut
from ._common import bearer_auth

router = Router(tags=["auth"])


@router.post("/auth/token", response=TokenOut, auth=None)
def auth_token(request: HttpRequest, payload: TokenIn):
    user = authenticate(request, username=payload.email, password=payload.password)
    if user is None:
        raise HttpError(401, "Invalid credentials")
    return token_response(user)


@router.post("/auth/refresh", response=TokenOut, auth=bearer_auth)
def auth_refresh(request: HttpRequest):
    """Trade a still-valid token for a fresh one."""
    return token_response(require_user(request))


@router.get("/me", response=ProfileOut, auth=bearer_auth)
def me(request: HttpRequest):
    user = require_user(request)
    return profile_out(user)


def profile_out(user: User) -> dict:
    profile = UserProfile.objects.filter(user=user).first()
    avatar_url = profile.avatar.url if profile is not None and profile.avatar else None
    return {"id": user.pk, "email": user.email, "avatar_url": avatar_url}
