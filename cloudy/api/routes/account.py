from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpRequest
from ninja import File, Router, UploadedFile
from PIL import Image

from .. import email_codes
from ..auth import require_user, revoke_access_tokens, token_response
from ..profiles import (
    check_password,
    clean_aerodrome,
    clean_birth_date,
    clean_name,
    clean_phone,
    email_taken,
    FieldErrors,
    invalid_credentials,
    pilot_profile,
    profile_to_dict,
    save_email_notifications,
    settings_to_dict,
)
from ..schemas.account import AvatarOut, PasswordChangeIn, ProfilePatchIn, SettingsOut, SettingsPatchIn
from ..schemas.auth import ProfileOut, TokenOut
from ._common import bearer_auth

router = Router(tags=["account"])

AVATAR_MAX_BYTES = 5 * 1024 * 1024


@router.get("/me", response=ProfileOut, auth=bearer_auth)
def me(request: HttpRequest):
    user = require_user(request)
    return profile_out(user)


def profile_out(user: User) -> dict:
    if getattr(user, "userprofile", None) is None:
        # Staff accounts have no pilot profile: only the account fields.
        return {"id": user.pk, "email": user.email, "avatar_url": None}
    return profile_to_dict(user)


@router.patch("/me", response=ProfileOut, auth=bearer_auth)
def patch_me(request: HttpRequest, payload: ProfilePatchIn):
    user = require_user(request)
    profile = pilot_profile(user)
    fields = payload.model_fields_set
    errors = FieldErrors()

    if "first_name" in fields:
        user.first_name = clean_name(payload.first_name, "first_name", errors).capitalize()
    if "last_name" in fields:
        user.last_name = clean_name(payload.last_name, "last_name", errors).upper()
    if "birth_date" in fields:
        profile.dob = clean_birth_date(payload.birth_date, errors)
    if "phone" in fields:
        profile.phone = clean_phone(payload.phone, errors)
    if "base_aerodrome" in fields:
        profile.aerodrom = clean_aerodrome(payload.base_aerodrome, errors)

    new_email = None
    if "email" in fields:
        new_email = email_codes.normalize_email(payload.email)
        if new_email == user.email.lower():
            new_email = None
        else:
            try:
                validate_email(new_email)
            except ValidationError:
                errors.add("email", "Enter a valid email address.", "invalid")
                new_email = None
    errors.raise_if_any("Invalid profile")

    if new_email:
        if not payload.current_password or not user.check_password(payload.current_password):
            raise invalid_credentials()
        if User.objects.filter(email__iexact=new_email).exclude(pk=user.pk).exists():
            raise email_taken()
        user.email = new_email

    # Only the columns edited here, so a concurrent password change is not overwritten.
    user.save(update_fields=["first_name", "last_name", "email"])
    profile.save(update_fields=["dob", "phone", "aerodrom"])
    return profile_to_dict(user)


@router.post("/me/avatar", response={201: AvatarOut}, auth=bearer_auth)
def upload_avatar(request: HttpRequest, file: UploadedFile = File(...)):
    user = require_user(request)
    profile = pilot_profile(user)
    errors = FieldErrors()
    if file.size and file.size > AVATAR_MAX_BYTES:
        errors.add("file", "The image must be 5 MB or less.", "max_size")
    else:
        try:
            Image.open(file).verify()
        # Pillow reports damaged files with several exception types (SyntaxError for a bad PNG CRC).
        except Exception:
            errors.add("file", "Send an image file (JPEG or PNG).", "invalid_image")
        file.seek(0)
    errors.raise_if_any("Invalid image")
    old = profile.avatar.name if profile.avatar else None
    profile.avatar = file
    profile.save(update_fields=["avatar"])
    if old and old != profile.avatar.name:
        profile.avatar.storage.delete(old)
    return 201, {"avatar_url": profile.avatar.url}


@router.delete("/me/avatar", response={204: None}, auth=bearer_auth)
def delete_avatar(request: HttpRequest):
    profile = pilot_profile(require_user(request))
    if profile.avatar:
        profile.avatar.delete(save=False)
        profile.avatar = None
        profile.save(update_fields=["avatar"])
    return 204, None


@router.post("/me/password", response=TokenOut, auth=bearer_auth)
def change_password(request: HttpRequest, payload: PasswordChangeIn):
    """Change the password. Older tokens stop working; the response carries a new one."""
    user = require_user(request)
    if not user.check_password(payload.current_password):
        raise invalid_credentials()
    errors = FieldErrors()
    check_password(payload.new_password, user, errors, field="new_password")
    errors.raise_if_any("Invalid password")
    user.set_password(payload.new_password)
    user.save(update_fields=["password"])
    revoke_access_tokens(user)
    return token_response(user)


@router.get("/me/settings", response=SettingsOut, auth=bearer_auth)
def get_settings(request: HttpRequest):
    return settings_to_dict(require_user(request))


@router.patch("/me/settings", response=SettingsOut, auth=bearer_auth)
def patch_settings(request: HttpRequest, payload: SettingsPatchIn):
    user = require_user(request)
    if payload.email_notifications is not None:
        save_email_notifications(user, payload.email_notifications)
    return settings_to_dict(user)
