from django.contrib.auth import authenticate
from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError

from ..auth import issue_access_token
from ..schemas.auth import TokenIn, TokenOut

router = Router(tags=["auth"])


@router.post("/auth/token", response=TokenOut, auth=None)
def auth_token(request: HttpRequest, payload: TokenIn):
    user = authenticate(request, username=payload.email, password=payload.password)
    if user is None:
        raise HttpError(401, "Invalid credentials")
    access_token, expires_in = issue_access_token(user)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user_id": user.pk,
    }
