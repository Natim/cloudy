"""Keyset pagination for log lists (newest first by flight date, then id)."""

import base64
import json
from datetime import datetime
from typing import Any

from django.db.models import Q
from django.utils.dateparse import parse_datetime

from .errors import invalid_payload


def _encode_token(date: datetime, log_id: int) -> str:
    payload = {"date": date.isoformat(), "id": log_id}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_page_token(token: str) -> tuple[datetime, int]:
    try:
        padded = token + "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
        dt = parse_datetime(data["date"])
        log_id = int(data["id"])
    except KeyError, TypeError, ValueError, json.JSONDecodeError:
        raise invalid_payload("Invalid page_token") from None
    if dt is None:
        raise invalid_payload("Invalid page_token")
    return dt, log_id


def parse_optional_iso_datetime(value: str | None, param: str) -> datetime | None:
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise invalid_payload(f"Invalid {param}") from exc
    return parsed


def paginate_logs_queryset(qs, *, limit: int, page_token: str | None):
    limit = max(1, min(limit, 200))
    qs = qs.order_by("-date", "-id")
    if page_token:
        cursor_date, cursor_id = decode_page_token(page_token)
        qs = qs.filter(Q(date__lt=cursor_date) | Q(date=cursor_date, id__lt=cursor_id))
    rows = list(qs[: limit + 1])
    next_token = None
    if len(rows) > limit:
        rows = rows[:limit]
        last = rows[-1]
        next_token = _encode_token(last.date, last.id)
    return rows, next_token


def log_list_response(items: list[dict[str, Any]], next_page_token: str | None) -> dict[str, Any]:
    return {"items": items, "next_page_token": next_page_token}
