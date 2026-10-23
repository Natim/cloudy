"""Build OpenAPI component schemas from log json_rules()."""

from typing import Any

from cloudy.logbooks import settings as book_settings

from .serialization import MODEL_TO_API

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
        api_name = MODEL_TO_API.get(name, name)
        prop = dict(_JSON_TYPE_MAP.get(rtype, {"type": "string"}))
        properties[api_name] = prop
        if write and name in {"date", "optional_filter"}:
            required.append(api_name if name == "date" else name)
    if write and "flight_date" in properties:
        required = [k for k in required if k != "date"]
        if "flight_date" not in required:
            required.append("flight_date")
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = sorted(set(required))
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
            "category": {"type": "string"},
            "time_format": {"type": "integer"},
            "height_format": {"type": "integer"},
            "created_at": {"type": "string", "format": "date-time"},
            "updated_at": {"type": "string", "format": "date-time"},
            "visible": {"type": "boolean"},
            "deleted": {"type": "boolean"},
        },
    }
    return schema
