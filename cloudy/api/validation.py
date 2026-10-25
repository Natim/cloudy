"""Validate API log and report payloads against json_rules()."""

from datetime import datetime
from typing import Any

from dateutil.parser import isoparse

from cloudy.logbooks.models import LogBase, LogBookBase

from .constants import READONLY_LOG_FIELDS
from .errors import invalid_payload
from .serialization import MODEL_TO_API, normalize_log_body, normalize_report_body


def _empty_default(rtype: str) -> Any:
    if rtype == "integer":
        return 0
    if rtype == "bool":
        return False
    if rtype == "list":
        return []
    return ""


def _coerce_value(rtype: str, value: Any, field_api: str) -> Any:
    if value is None:
        if rtype in {"string", "list"}:
            return _empty_default(rtype)
        raise invalid_payload(
            "Invalid log", errors={field_api: [{"message": "This field may not be null.", "code": "null"}]}
        )
    if rtype == "date":
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return isoparse(value)
            except (TypeError, ValueError) as exc:
                raise invalid_payload(
                    "Invalid log",
                    errors={field_api: [{"message": "Invalid date-time.", "code": "invalid"}]},
                ) from exc
    if rtype == "integer":
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise invalid_payload(
                "Invalid log",
                errors={field_api: [{"message": "A valid integer is required.", "code": "invalid"}]},
            ) from exc
    if rtype == "bool":
        if isinstance(value, bool):
            return value
        raise invalid_payload(
            "Invalid log",
            errors={field_api: [{"message": "Must be a boolean.", "code": "invalid"}]},
        )
    if rtype == "list":
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return value.split(";") if value else []
        raise invalid_payload(
            "Invalid log",
            errors={field_api: [{"message": "Must be a list.", "code": "invalid"}]},
        )
    return value


def allowed_log_api_keys(logbook: LogBookBase) -> set[str]:
    sample = logbook._log_model()()
    keys: set[str] = set()
    for rule in sample.json_rules():
        name = rule[0]
        if name in READONLY_LOG_FIELDS:
            continue
        keys.add(name)
        keys.add(MODEL_TO_API.get(name, name))
    return keys


def _writable_rules(logbook: LogBookBase) -> list[tuple[str, str]]:
    sample = logbook._log_model()()
    return [rule for rule in sample.json_rules() if rule[0] not in READONLY_LOG_FIELDS]


def validate_and_prepare_log_body(
    logbook: LogBookBase,
    body: dict[str, Any],
    *,
    partial: bool,
    log: LogBase | None = None,
) -> dict[str, Any]:
    allowed = allowed_log_api_keys(logbook)
    unknown = [key for key in body if key not in allowed]
    if unknown:
        raise invalid_payload(
            "Invalid log",
            errors={key: [{"message": "Unknown field.", "code": "unknown"}] for key in unknown},
        )

    normalized = normalize_log_body(body, logbook.cat)
    if partial and log is not None:
        prepared = {}
        for name, rtype in _writable_rules(logbook):
            if name not in normalized:
                continue
            api_name = MODEL_TO_API.get(name, name)
            prepared[name] = _coerce_value(rtype, normalized[name], api_name)
        return prepared

    prepared = {}
    for name, rtype in _writable_rules(logbook):
        api_name = MODEL_TO_API.get(name, name)
        if name in normalized:
            prepared[name] = _coerce_value(rtype, normalized[name], api_name)
        else:
            prepared[name] = _empty_default(rtype)

    if "date" not in prepared or not prepared["date"]:
        raise invalid_payload(
            "Invalid log",
            errors={"flight_date": [{"message": "This field is required.", "code": "required"}]},
        )
    return prepared


def allowed_report_api_keys(logbook: LogBookBase) -> set[str]:
    form_class = logbook._report_form_model()
    keys: set[str] = set()
    for name in form_class(logbook).fields.keys():
        keys.add(name)
        keys.add(MODEL_TO_API.get(name, name))
    return keys


def validate_report_body(logbook: LogBookBase, body: dict[str, Any]) -> dict[str, Any]:
    api_allowed = allowed_report_api_keys(logbook)
    unknown = [key for key in body if key not in api_allowed]
    if unknown:
        raise invalid_payload(
            "Invalid report",
            errors={key: [{"message": "Unknown field.", "code": "unknown"}] for key in unknown},
        )
    return normalize_report_body(body)
