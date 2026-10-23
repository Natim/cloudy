"""Map API JSON (model json_rules shape) to Django log forms."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from dateutil.parser import isoparse
from django.http import QueryDict

from cloudy.logbooks.models import LogBase, LogBookBase
from cloudy.time_format.formatters import HhmmFormatter, TenthFormatter

READONLY_LOG_FIELDS = frozenset({"id", "lbook", "cdate", "update", "deleted", "files", "visbl"})

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


def _coerce_body_value(rtype: str, value: Any) -> Any:
    if value is None:
        return ""
    if rtype == "date":
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return isoparse(value)
    if rtype == "integer":
        return int(value)
    if rtype == "bool":
        return bool(value)
    if rtype == "list":
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return value.split(";") if value else []
    return value


def _apply_body_to_log(log: LogBase, body: dict[str, Any]) -> None:
    for rule in log.json_rules():
        name, rtype = rule[0], rule[1]
        if name in READONLY_LOG_FIELDS:
            continue
        if name not in body:
            continue
        setattr(log, name, _coerce_body_value(rtype, body[name]))


def _unsaved_log(logbook: LogBookBase) -> LogBase:
    log_model = logbook._log_model()
    now = datetime.now()
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
    """Build POST data for the logbook's form from an API payload."""
    instance = log if log is not None else _unsaved_log(logbook)
    _apply_body_to_log(instance, body)

    form_class = logbook._log_form_model()
    form = form_class(logbook, log=instance)
    data: dict[str, Any] = dict(form.initial or {})

    for rule in instance.json_rules():
        name, rtype = rule[0], rule[1]
        if name in READONLY_LOG_FIELDS or name not in body:
            continue
        value = _coerce_body_value(rtype, body[name])
        form_name = _DGAC_FIELD_ALIASES.get(name, name)
        if rtype == "date" and isinstance(value, datetime):
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
        if isinstance(val, datetime):
            qd[key] = val.strftime("%d/%m/%Y")
        else:
            qd[key] = str(val)
    return qd


def save_log_from_api(user, logbook: LogBookBase, body: dict[str, Any], log: LogBase | None = None):
    form_class = logbook._log_form_model()
    post = body_to_form_data(logbook, body, log=log)
    form = form_class(logbook, post, log=log)
    if not form.is_valid():
        raise ValueError(form.errors.as_json())
    saved = form.save(user, logbook, {}, log)
    saved.save()
    return LogBase.get_by_id(saved.pk)
