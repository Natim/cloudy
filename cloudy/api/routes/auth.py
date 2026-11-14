from constance import config
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError

from cloudy.accounts.models import EmailCode, UserProfile

from .. import email_codes
from ..auth import require_user, revoke_access_tokens, token_response
from ..errors import ApiHttpError
from ..profiles import (
    active_user_for_email,
    check_password,
    clean_aerodrome,
    clean_birth_date,
    clean_name,
    clean_phone,
    create_account,
    email_taken,
    FieldErrors,
)
from ..schemas.auth import (
    CodeIn,
    CompleteRegistrationIn,
    EmailIn,
    ProfileOut,
    ResetPasswordIn,
    TokenIn,
    TokenOut,
)
from ._common import bearer_auth

router = Router(tags=["auth"])

CODE_SENT = {"detail": "Code sent", "expires_in": int(email_codes.CODE_TTL.total_seconds())}


def _valid_email(raw: str) -> str:
    email = email_codes.normalize_email(raw)
    try:
        validate_email(email)
    except ValidationError:
        errors = FieldErrors()
        errors.add("email", "Enter a valid email address.", "invalid")
        errors.raise_if_any("Invalid email")
    return email


def _too_many_requests() -> ApiHttpError:
    return ApiHttpError(429, "Wait a minute before asking for another code", code="rate_limited")


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


@router.post("/auth/register", response=dict, auth=None)
def auth_register(request: HttpRequest, payload: EmailIn):
    """Mail a sign-up code. Also used to ask for a new one."""
    email = _valid_email(payload.email)
    if not config.SIGNUP_AUTHORIZED:
        raise ApiHttpError(403, "Sign-up is closed", code="signup_closed")
    if active_user_for_email(email) is not None:
        raise email_taken()
    if email_codes.recently_sent(email, EmailCode.SIGNUP):
        raise _too_many_requests()
    email_codes.issue_code(email, EmailCode.SIGNUP)
    return CODE_SENT


@router.post("/auth/verify-otp", response=dict, auth=None)
def auth_verify_otp(request: HttpRequest, payload: CodeIn):
    """Check a sign-up or password-reset code without using it up."""
    email = email_codes.normalize_email(payload.email)
    email_codes.check_code(email, payload.otp, (EmailCode.SIGNUP, EmailCode.PASSWORD_RESET))
    return {"valid": True}


@router.post("/auth/complete-registration", response={201: TokenOut}, auth=None)
def auth_complete_registration(request: HttpRequest, payload: CompleteRegistrationIn):
    email = _valid_email(payload.email)
    if not config.SIGNUP_AUTHORIZED:
        raise ApiHttpError(403, "Sign-up is closed", code="signup_closed")
    if active_user_for_email(email) is not None:
        raise email_taken()
    code = email_codes.check_code(email, payload.otp, (EmailCode.SIGNUP,))

    errors = FieldErrors()
    first_name = clean_name(payload.first_name, "first_name", errors)
    last_name = clean_name(payload.last_name, "last_name", errors)
    birth_date = clean_birth_date(payload.birth_date, errors)
    phone = clean_phone(payload.phone, errors)
    base_aerodrome = clean_aerodrome(payload.base_aerodrome, errors)
    errors.raise_if_any("Invalid registration")
    check_password(payload.password, User(email=email, first_name=first_name, last_name=last_name), errors)
    errors.raise_if_any("Invalid registration")

    user = create_account(
        request,
        email=email,
        password=payload.password,
        first_name=first_name,
        last_name=last_name,
        birth_date=birth_date,
        phone=phone,
        base_aerodrome=base_aerodrome,
    )
    email_codes.consume(code)
    return 201, token_response(user)


@router.post("/auth/forgot-password", response=dict, auth=None)
def auth_forgot_password(request: HttpRequest, payload: EmailIn):
    """Always answers the same way, so it never tells whether an account exists."""
    email = email_codes.normalize_email(payload.email)
    if active_user_for_email(email) is not None and not email_codes.recently_sent(
        email, EmailCode.PASSWORD_RESET
    ):
        email_codes.issue_code(email, EmailCode.PASSWORD_RESET)
    return CODE_SENT


@router.post("/auth/reset-password", response=TokenOut, auth=None)
def auth_reset_password(request: HttpRequest, payload: ResetPasswordIn):
    email = email_codes.normalize_email(payload.email)
    user = active_user_for_email(email)
    if user is None:
        raise email_codes.otp_expired()
    code = email_codes.check_code(email, payload.otp, (EmailCode.PASSWORD_RESET,))
    errors = FieldErrors()
    check_password(payload.password, user, errors)
    errors.raise_if_any("Invalid password")
    user.set_password(payload.password)
    user.save(update_fields=["password"])
    revoke_access_tokens(user)
    email_codes.consume(code)
    return token_response(user)


@router.get("/me", response=ProfileOut, auth=bearer_auth)
def me(request: HttpRequest):
    user = require_user(request)
    return profile_out(user)


def profile_out(user: User) -> dict:
    profile = UserProfile.objects.filter(user=user).first()
    avatar_url = profile.avatar.url if profile is not None and profile.avatar else None
    return {"id": user.pk, "email": user.email, "avatar_url": avatar_url}
