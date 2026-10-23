"""Build OpenAPI component schemas from log json_rules()."""

from __future__ import annotations

from typing import Any

from cloudy.logbooks import settings as book_settings

_JSON_TYPE_MAP = {
    "string": {"type": "string"},
    "integer": {"type": "integer"},
    "bool": {"type": "boolean"},
    "date": {"type": "string", "format": "date-time"},
    "list": {"type": "array", "items": {"type": "string"}},
    "fk": {"type": "integer"},
}


def _sample_log_for_cat(cat: str):
    book_class = book_settings.MAP[cat]
    return book_class._log_model()()


def log_schema_for_cat(cat: str, *, write: bool = False) -> dict[str, Any]:
    log = _sample_log_for_cat(cat)
    properties: dict[str, Any] = {}
    required: list[str] = []
    for rule in log.json_rules():
        name, rtype = rule[0], rule[1]
        if write and name in {
            "id",
            "lbook",
            "cdate",
            "update",
            "deleted",
            "files",
            "visbl",
        }:
            continue
        prop = dict(_JSON_TYPE_MAP.get(rtype, {"type": "string"}))
        properties[name] = prop
        if write and name in {"date", "optional_filter"}:
            required.append(name)
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def enrich_openapi_schema(schema: dict[str, Any]) -> dict[str, Any]:
    components = schema.setdefault("components", {}).setdefault("schemas", {})
    for cat in book_settings.MAP:
        components[f"LogRead_{cat}"] = log_schema_for_cat(cat, write=False)
        components[f"LogWrite_{cat}"] = log_schema_for_cat(cat, write=True)
    components["Logbook"] = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "cat": {"type": "string"},
            "time_format": {"type": "integer"},
            "height_format": {"type": "integer"},
            "cdate": {"type": "string", "format": "date-time"},
            "update": {"type": "string", "format": "date-time"},
            "visbl": {"type": "boolean"},
            "deleted": {"type": "boolean"},
        },
    }
    return schema
