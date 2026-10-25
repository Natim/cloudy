"""Map API JSON (model json_rules shape) to Django log forms."""

from typing import Any

from django.http import QueryDict
from django.utils import timezone

from cloudy.logbooks.models import LogBase, LogBookBase
from cloudy.time_format.formatters import HhmmFormatter, TenthFormatter

from .constants import READONLY_LOG_FIELDS
from .errors import invalid_payload
from .serialization import MODEL_TO_API
from .validation import validate_and_prepare_log_body

# API aliases for form-only field names on DGAC avion.
_DGAC_FIELD_ALIASES = {
    "aeronef_type": "ltype",
    "aeronef_imma": "imma",
    "fctbrd": "fboard",
    "natvol": "nvol",
    "airpdep": "aerostart",
    "airpar": "aeroend",
    "cmmts": "coms",
    "nbrto": "takeoffcount",
    "nbrla": "landingcount",
}


def _apply_body_to_log(log: LogBase, body: dict[str, Any]) -> None:
    for rule in log.json_rules():
        name, rtype = rule[0], rule[1]
        if name in READONLY_LOG_FIELDS:
            continue
        if name not in body:
            continue
        value = body[name]
        if rtype == "list":
            if isinstance(value, list):
                setattr(log, name, ";".join(value))
            else:
                setattr(log, name, value or "")
            continue
        setattr(log, name, value)


def _unsaved_log(logbook: LogBookBase) -> LogBase:
    log_model = logbook._log_model()
    now = timezone.now()
    return log_model(
        lbook=logbook,
        cdate=now,
        update=now,
        date=now,
        optional_filter="",
        airpdep="",
        airpar="",
        visbl=True,
        deleted=False,
    )


def body_to_form_data(logbook: LogBookBase, body: dict[str, Any], log: LogBase | None = None) -> QueryDict:
    """Build POST data for the logbook's form from an API payload (model field names)."""
    instance = log if log is not None else _unsaved_log(logbook)
    _apply_body_to_log(instance, body)

    form_class = logbook._log_form_model()
    form = form_class(logbook, log=instance)
    data: dict[str, Any] = dict(form.initial or {})

    for rule in instance.json_rules():
        name, rtype = rule[0], rule[1]
        if name in READONLY_LOG_FIELDS or name not in body:
            continue
        value = body[name]
        form_name = _DGAC_FIELD_ALIASES.get(name, name)
        if rtype == "date" and hasattr(value, "strftime"):
            data[form_name] = value.strftime("%d/%m/%Y")
        elif form_name in {"departure_time", "arrival_time"} and isinstance(value, str) and ":" in value:
            hours, mins = value.split(":", 1)
            data[f"{form_name}_0"] = hours
            data[f"{form_name}_1"] = mins
        elif rtype == "list" and isinstance(value, list):
            for idx, passenger in enumerate(value[:3]):
                data[f"passenger{chr(65 + idx)}"] = passenger
        else:
            data[form_name] = value

    if log is not None:
        data["log_id"] = str(log.id)

    qd = QueryDict(mutable=True)
    time_field_names = set(getattr(form_class, "timefields", {}).keys())
    for key, val in data.items():
        if val is None:
            val = ""
        if key.endswith("_0") or key.endswith("_1"):
            qd[key] = str(val)
            continue
        if key in time_field_names and val != "":
            minutes = int(val)
            if logbook.time_format == 0:
                hours, mins = HhmmFormatter.output(minutes).split(":")
                qd[f"{key}_0"] = hours
                qd[f"{key}_1"] = mins
            else:
                qd[key] = TenthFormatter.output(minutes)
            continue
        if hasattr(val, "strftime"):
            qd[key] = val.strftime("%d/%m/%Y")
        else:
            qd[key] = str(val)
    return qd


def form_errors_to_api(form_errors) -> dict:
    form_to_model = {v: k for k, v in _DGAC_FIELD_ALIASES.items()}
    out: dict = {}
    for field, entries in form_errors.get_json_data().items():
        model_name = form_to_model.get(field, field)
        api_name = MODEL_TO_API.get(model_name, field)
        out[api_name] = entries
    return out


def save_log_from_api(
    user,
    logbook: LogBookBase,
    body: dict[str, Any],
    log: LogBase | None = None,
    *,
    partial: bool = False,
):
    prepared = validate_and_prepare_log_body(logbook, body, partial=partial, log=log)
    if partial and not prepared:
        raise invalid_payload("Empty patch body")
    form_class = logbook._log_form_model()
    post = body_to_form_data(logbook, prepared, log=log)
    form = form_class(logbook, post, log=log)
    if not form.is_valid():
        raise invalid_payload("Invalid log", errors=form_errors_to_api(form.errors))
    saved = form.save(user, logbook, {}, log)
    saved.save()
    return LogBase.get_by_id(saved.pk)
