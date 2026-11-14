from datetime import date

from ninja import Schema


class ProfilePatchIn(Schema):
    first_name: str | None = None
    last_name: str | None = None
    birth_date: date | None = None
    phone: str | None = None
    base_aerodrome: str | None = None
    email: str | None = None
    # Required only when the email changes.
    current_password: str | None = None


class PasswordChangeIn(Schema):
    current_password: str
    new_password: str


class AccountDeleteIn(Schema):
    password: str


class SettingsPatchIn(Schema):
    email_notifications: bool | None = None


class AvatarOut(Schema):
    avatar_url: str


class SettingsOut(Schema):
    email_notifications: bool
