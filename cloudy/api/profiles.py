"""Account data for the mobile API: validation, serialization and creation."""

import re
from datetime import date
from typing import Any

from constance import config
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django_registration.signals import user_registered

from cloudy.accounts.forms import generate_username, validate_minimum_pilot_age
from cloudy.accounts.models import ProfileSettings, UserProfile
from cloudy.notifications.models import NoticeSetting, NoticeType

from .errors import ApiHttpError, invalid_payload

NAME_MAX_LENGTH = 30
AERODROME_MAX_LENGTH = 30
PHONE_PATTERN = re.compile(r"^\+?[0-9]{6,19}$")


class FieldErrors:
    """Collect per-field messages in the shape the rest of the API returns."""

    def __init__(self):
        self.errors: dict[str, list[dict[str, str]]] = {}

    def add(self, field: str, message: str, code: str = "invalid") -> None:
        self.errors.setdefault(field, []).append({"message": message, "code": code})

    def raise_if_any(self, detail: str = "Invalid payload") -> None:
        if self.errors:
            raise invalid_payload(detail, errors=self.errors)


def email_taken() -> ApiHttpError:
    return ApiHttpError(409, "An account already exists with this email", code="EMAIL_TAKEN")


def invalid_credentials() -> ApiHttpError:
    return ApiHttpError(401, "Invalid credentials", code="invalid_credentials")


def active_user_for_email(email: str) -> User | None:
    return User.objects.filter(email__iexact=email, is_active=True).order_by("-last_login", "-pk").first()


def clean_name(value: str | None, field: str, errors: FieldErrors) -> str:
    value = (value or "").strip()
    if not value:
        errors.add(field, "This field is required.", "required")
    elif len(value) > NAME_MAX_LENGTH:
        errors.add(field, f"At most {NAME_MAX_LENGTH} characters.", "max_length")
    return value


def clean_birth_date(value: date | None, errors: FieldErrors) -> date | None:
    if value is None:
        errors.add("birth_date", "This field is required.", "required")
        return None
    try:
        validate_minimum_pilot_age(value)
    except forms.ValidationError:
        errors.add("birth_date", "You must be at least 14 years old.", "min_age")
    return value


def clean_phone(value: str | None, errors: FieldErrors) -> str:
    value = re.sub(r"[\s.\-()]", "", value or "")
    if value and not PHONE_PATTERN.match(value):
        errors.add("phone", "Use the international format, e.g. +33612345678.", "invalid")
    return value


def clean_aerodrome(value: str | None, errors: FieldErrors) -> str:
    value = (value or "").strip().upper()
    if len(value) > AERODROME_MAX_LENGTH:
        errors.add("base_aerodrome", f"At most {AERODROME_MAX_LENGTH} characters.", "max_length")
    return value


def check_password(password: str, user: User | None, errors: FieldErrors, field: str = "password") -> None:
    try:
        validate_password(password, user)
    except ValidationError as exc:
        for item in exc.error_list:
            errors.add(field, " ".join(item.messages), item.code or "invalid")


def pilot_profile(user: User) -> UserProfile:
    profile = getattr(user, "userprofile", None)
    if profile is None:
        raise ApiHttpError(409, "This account has no pilot profile", code="profile_missing")
    return profile


def storage_to_dict(profile: UserProfile) -> dict[str, Any]:
    """Space used and the quota it counts against; First Class storage is unlimited."""
    free_limit = int(config.DISKSPACE_FREE_MAXMB) * 1024 * 1024
    return {
        "used_bytes": max(0, profile.disk_space_balance),
        "limit_bytes": None if profile.has_payed_plan() else free_limit,
    }


def profile_to_dict(user: User) -> dict[str, Any]:
    profile = pilot_profile(user)
    return {
        "id": user.pk,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "birth_date": profile.dob.isoformat() if profile.dob else None,
        "phone": profile.phone,
        "base_aerodrome": profile.aerodrom,
        "avatar_url": profile.avatar.url if profile.avatar else None,
        "plan": "first" if profile.has_payed_plan() else "economy",
        "plan_since": profile.fplan_switch_date.isoformat()
        if profile.has_payed_plan() and profile.fplan_switch_date
        else None,
        "date_joined": user.date_joined.isoformat(),
        "storage": storage_to_dict(profile),
    }


def settings_to_dict(user: User) -> dict[str, Any]:
    prefs = ProfileSettings.objects.filter(user=user).first()
    return {"email_notifications": prefs.mail_on_notification if prefs else True}


def save_email_notifications(user: User, enabled: bool) -> None:
    """Same effect as the web account settings form (ProfileSettingsForm.save)."""
    for notice_type in NoticeType.objects.all():
        if notice_type.label not in settings.NOTICE_TYPE_IGNORE:
            notice_setting = NoticeSetting.for_user(user, notice_type, 0)
            notice_setting.send = enabled
            notice_setting.save()
    prefs, _created = ProfileSettings.objects.get_or_create(user=user)
    prefs.mail_on_notification = enabled
    prefs.save()


@transaction.atomic
def create_account(
    request,
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    birth_date: date,
    phone: str,
    base_aerodrome: str,
) -> User:
    """Create an active account once the email is proven by a code.

    A web sign-up that was never activated is taken over: the code proves the
    same person owns the address.
    """
    first_name = first_name.capitalize()
    last_name = last_name.upper()
    user = User.objects.filter(email__iexact=email, is_active=False).order_by("-pk").first()
    if user is None:
        user = User(email=email, username=generate_username(last_name))
    user.first_name = first_name
    user.last_name = last_name
    user.is_active = True
    user.set_password(password)
    user.save()

    profile = UserProfile.objects.filter(user=user).first() or UserProfile(user=user, dob=birth_date)
    profile.dob = birth_date
    profile.phone = phone
    profile.aerodrom = base_aerodrome
    profile.save()
    if not profile.api_key:
        profile.generate_api_key()

    user_registered.send(sender=create_account, user=user, request=request)
    return user
