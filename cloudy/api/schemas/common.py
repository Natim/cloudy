from typing import Any

from ninja import Schema


class ErrorOut(Schema):
    detail: str
    code: str | None = None
    errors: dict[str, Any] | None = None


class LogListOut(Schema):
    items: list[dict[str, Any]]
    next_page_token: str | None = None
