"""External JSON names for the mobile API (English, stable)."""

from typing import Any

from cloudy.logbooks.models import LogBookBase

# Internal model / legacy field name -> public API name.
MODEL_TO_API: dict[str, str] = {
    "cat": "category",
    "cdate": "created_at",
    "update": "updated_at",
    "visbl": "visible",
    "lbook": "logbook_id",
    "date": "flight_date",
    "airpdep": "departure_airport",
    "airpar": "arrival_airport",
    "aeronef_type": "aircraft_type",
    "aeronef_imma": "aircraft_registration",
    "aircraft_imma": "aircraft_registration",
    "ulm_type": "aircraft_type",
    "ulm_imma": "aircraft_registration",
    "glider_type": "aircraft_type",
    "glider_imma": "aircraft_registration",
    "fctbrd": "function_on_board",
    "natvol": "flight_nature",
    "cmmts": "comments",
    "nbrto": "takeoff_count",
    "nbrla": "landing_count",
    "staffob": "passengers",
    "obs": "observations",
    "simu": "simulator_minutes",
    "imma": "registration",
    "mbr_equipage_jour": "crew_day_minutes",
    "mbr_equipage_nuit": "crew_night_minutes",
    "mono_jdbl": "single_engine_day_dual_minutes",
    "mono_jcdb": "single_engine_day_captain_minutes",
    "mono_ndbl": "single_engine_night_dual_minutes",
    "mono_ncdb": "single_engine_night_captain_minutes",
    "mul_jdbl": "multi_engine_day_dual_minutes",
    "mul_jcdb": "multi_engine_day_captain_minutes",
    "mul_jcplt": "multi_engine_day_co_pilot_minutes",
    "mul_ndbl": "multi_engine_night_dual_minutes",
    "mul_ncdb": "multi_engine_night_captain_minutes",
    "mul_ncplt": "multi_engine_night_co_pilot_minutes",
    "vai_dbl": "instrument_day_dual_minutes",
    "vai_plt": "instrument_pilot_minutes",
    "flytime_dbl": "dual_minutes",
    "flytime_cdb": "pilot_in_command_minutes",
    "flytime_ins": "instructor_minutes",
    "name_pic": "pilot_in_command_name",
    "pilot_timpe_cop": "co_pilot_minutes",
    "path": "url",
}

API_TO_MODEL: dict[str, str] = {}
for model_name, api_name in MODEL_TO_API.items():
    API_TO_MODEL.setdefault(api_name, model_name)

_AIRCRAFT_TYPE_FIELDS = {
    "plane_dgac": "aeronef_type",
    "helicopter_dgac": "aeronef_type",
    "plane_fcl1080": "aircraft_type",
    "ulm_ffplum": "ulm_type",
    "glider_dgac": "glider_type",
    "balloon_dgac": "ballon_type",
    "parachute_cloudy": "aircraft",
}

_AIRCRAFT_REG_FIELDS = {
    "plane_dgac": "aeronef_imma",
    "helicopter_dgac": "aeronef_imma",
    "plane_fcl1080": "aircraft_imma",
    "ulm_ffplum": "ulm_imma",
    "glider_dgac": "glider_imma",
    "balloon_dgac": "ballon_imma",
}


def logbook_to_dict(logbook: LogBookBase) -> dict[str, Any]:
    return {
        "id": logbook.id,
        "name": logbook.name,
        "category": logbook.cat,
        "time_format": logbook.time_format,
        "height_format": logbook.height_format,
        "created_at": logbook.cdate.isoformat(),
        "updated_at": logbook.update.isoformat(),
        "visible": logbook.visbl,
        "deleted": logbook.deleted,
    }


def _rename_keys(data: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        api_key = mapping.get(key, key)
        if key == "files" and isinstance(value, list):
            out["files"] = [_rename_keys(item, mapping) if isinstance(item, dict) else item for item in value]
        else:
            out[api_key] = value
    return out


def log_to_api_dict(raw: dict[str, Any]) -> dict[str, Any]:
    return _rename_keys(raw, MODEL_TO_API)


def log_instance_to_api_dict(log) -> dict[str, Any]:
    from django.conf import settings

    raw = log.to_json(serialize=False)
    raw["files"] = [
        {"id": fobject.pk, "path": f"{settings.MEDIA_URL}{fobject.file.name}"}
        for fobject in log.files.filter(deleted=False)
    ]
    return log_to_api_dict(raw)


def normalize_report_body(body: dict[str, Any]) -> dict[str, Any]:
    return {API_TO_MODEL.get(key, key): value for key, value in body.items()}


def reports_to_api_dict(reports: dict[str, Any] | None) -> dict[str, Any]:
    if not reports:
        return {}
    return {MODEL_TO_API.get(key, key): value for key, value in reports.items()}


def normalize_log_body(body: dict[str, Any], category: str | None = None) -> dict[str, Any]:
    """Accept public API names (and legacy model names) on write."""
    out: dict[str, Any] = {}
    for key, value in body.items():
        if key == "aircraft_type" and category:
            out[_AIRCRAFT_TYPE_FIELDS.get(category, "aircraft_type")] = value
            continue
        if key == "aircraft_registration" and category:
            out[_AIRCRAFT_REG_FIELDS.get(category, "aircraft_imma")] = value
            continue
        model_key = API_TO_MODEL.get(key, key)
        out[model_key] = value
    return out


def aircraft_to_dict(aircraft) -> dict[str, Any]:
    return {
        "id": aircraft.id,
        "registration": aircraft.imma,
        "aircraft_type": aircraft.type,
        "airport": aircraft.airport,
        "photo_url": aircraft.get_photo().url if aircraft.get_photo() else None,
    }
