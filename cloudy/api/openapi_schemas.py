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
        if name == "synthetic_date":
            prop["nullable"] = True
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


def _log_read_one_of() -> dict[str, Any]:
    return {"oneOf": [{"$ref": f"#/components/schemas/LogRead_{cat}"} for cat in book_settings.MAP]}


def _log_write_one_of() -> dict[str, Any]:
    return {"oneOf": [{"$ref": f"#/components/schemas/LogWrite_{cat}"} for cat in book_settings.MAP]}


def _response_json_schema(operation: dict[str, Any], status: int) -> dict[str, Any]:
    """Ninja keys OpenAPI responses by int status until JSON encoding."""
    responses = operation["responses"]
    body = responses.get(status)
    if body is None:
        body = responses[str(status)]
    return body["content"]["application/json"]


def _patch_log_paths(schema: dict[str, Any]) -> None:
    paths = schema.get("paths", {})
    for path_key, methods in paths.items():
        if path_key.endswith("/logs/{log_id}"):
            for verb in ("get", "put", "patch"):
                if verb not in methods:
                    continue
                if verb in {"put", "patch"}:
                    content = methods[verb].setdefault("requestBody", {}).setdefault("content", {})
                    content.setdefault("application/json", {})["schema"] = _log_write_one_of()
                _response_json_schema(methods[verb], 200)["schema"] = _log_read_one_of()
            continue
        if not path_key.endswith("/logs"):
            continue
        if "get" in methods:
            _response_json_schema(methods["get"], 200)["schema"] = {"$ref": "#/components/schemas/LogListOut"}
        if "post" in methods:
            content = methods["post"].setdefault("requestBody", {}).setdefault("content", {})
            content.setdefault("application/json", {})["schema"] = _log_write_one_of()
            _response_json_schema(methods["post"], 201)["schema"] = _log_read_one_of()


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
    components["LogListOut"] = {
        "type": "object",
        "properties": {
            "items": {"type": "array", "items": _log_read_one_of()},
            "next_page_token": {"type": "string", "nullable": True},
        },
        "required": ["items", "next_page_token"],
    }
    _patch_log_paths(schema)
    return schema
