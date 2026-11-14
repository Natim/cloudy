from datetime import date

from ninja import Schema
from pydantic import AliasChoices, ConfigDict, Field


class TokenIn(Schema):
    email: str
    password: str


class TokenOut(Schema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int


class ProfileOut(Schema):
    id: int
    email: str
    avatar_url: str | None = None


class EmailIn(Schema):
    email: str


class CodeIn(Schema):
    email: str
    otp: str


class CompleteRegistrationIn(Schema):
    """Accepts snake_case and the camelCase names the mobile app sends."""

    model_config = ConfigDict(populate_by_name=True)

    email: str
    otp: str
    password: str
    first_name: str = Field(validation_alias=AliasChoices("first_name", "firstName"))
    last_name: str = Field(validation_alias=AliasChoices("last_name", "lastName"))
    birth_date: date | None = Field(default=None, validation_alias=AliasChoices("birth_date", "birthDate"))
    phone: str | None = Field(default=None, validation_alias=AliasChoices("phone", "phoneNumber"))
    base_aerodrome: str | None = Field(
        default=None, validation_alias=AliasChoices("base_aerodrome", "baseAerodrome")
    )


class ResetPasswordIn(Schema):
    email: str
    otp: str
    password: str
