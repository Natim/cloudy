"""
Convert DGAC Avion log entries to FCL 1.080 field values.

Used when duplicating a plane_dgac logbook into plane_fcl1080.
"""

from __future__ import annotations

import re
from typing import Any

from cloudy.DGAC_avion_logbook.models import DGACAvionLog
from cloudy.logbooks.icao import icao_from_place

OBS_TIME_RANGE_RE = re.compile(
    r"^\s*(\d{1,2})[:.]?(\d{2})\s*[-–]\s*(\d{1,2})[:.]?(\d{2})\s*$",
    re.IGNORECASE,
)

FCL_CMTS_MAX_LEN = 400
FCL_NAME_PIC_MAX_LEN = 30

# Normalized role keys returned by normalize_fctbrd().
ROLE_INST = "inst"
ROLE_EP = "ep"
ROLE_CDB = "cdb"
ROLE_PILOTE = "pilote"
ROLE_COPILOT = "copilot"
ROLE_EXAM = "exam"


def normalize_fctbrd(fctbrd: str) -> str:
    """Normalize Fonction à bord values (case-insensitive, typo variants)."""
    if not fctbrd:
        return ""
    key = fctbrd.strip().lower()
    if key in {"inst", "instructeur"}:
        return ROLE_INST
    if key in {"ep", "élève pilote", "eleve pilote"}:
        return ROLE_EP
    if key in {"cdb", "cbd", "commandant de bord"}:
        return ROLE_CDB
    if key == "pilote":
        return ROLE_PILOTE
    if key in {"co-pilote", "copilote", "co pilote"}:
        return ROLE_COPILOT
    if key in {"exam", "examinateur"}:
        return ROLE_EXAM
    return key


def parse_obs_times(obs: str) -> tuple[int, int]:
    """
    Parse clock times from DGAC observations when they look like a time range.

    Examples: ``09:30 - 09:55``, ``0700 - 0807``, ``1335-1359``.
    Returns (departure_minutes, arrival_minutes) from midnight, or (0, 0).
    """
    if not obs:
        return 0, 0
    match = OBS_TIME_RANGE_RE.match(obs.strip())
    if not match:
        return 0, 0
    h1, m1, h2, m2 = (int(x) for x in match.groups())
    if not (0 <= h1 <= 23 and 0 <= m1 <= 59 and 0 <= h2 <= 23 and 0 <= m2 <= 59):
        return 0, 0
    return h1 * 60 + m1, h2 * 60 + m2


def _mono_minutes(log: DGACAvionLog) -> int:
    return log.mono_jdbl + log.mono_jcdb + log.mono_ndbl + log.mono_ncdb


def _mul_minutes(log: DGACAvionLog) -> int:
    return log.mul_jdbl + log.mul_jcdb + log.mul_jcplt + log.mul_ndbl + log.mul_ncdb + log.mul_ncplt


def _flight_total_minutes(log: DGACAvionLog) -> int:
    return (
        _mono_minutes(log) + _mul_minutes(log) + (log.mbr_equipage_jour or 0) + (log.mbr_equipage_nuit or 0)
    )


def _day_minutes(log: DGACAvionLog) -> int:
    return log.mono_jdbl + log.mono_jcdb + log.mul_jdbl + log.mul_jcdb + log.mul_jcplt


def _night_minutes(log: DGACAvionLog) -> int:
    return log.mono_ndbl + log.mono_ncdb + log.mul_ndbl + log.mul_ncdb + log.mul_ncplt


def _cdb_minutes(log: DGACAvionLog) -> int:
    return log.mono_jcdb + log.mono_ncdb + log.mul_jcdb + log.mul_ncdb


def _dual_minutes(log: DGACAvionLog) -> int:
    return log.mono_jdbl + log.mono_ndbl + log.mul_jdbl + log.mul_ndbl


def _copilot_minutes(log: DGACAvionLog) -> int:
    return log.mul_jcplt + log.mul_ncplt


def _first_staff_name(staffob: str) -> str:
    if not staffob:
        return ""
    for part in staffob.split(";"):
        name = part.strip()
        if name:
            return name[:FCL_NAME_PIC_MAX_LEN]
    return ""


def _build_remarks(log: DGACAvionLog) -> str:
    obs = (log.obs or "").strip()
    natvol = (log.natvol or "").strip()
    if natvol and natvol not in obs:
        if obs:
            combined = f"{natvol} — {obs}"
        else:
            combined = natvol
        return combined[:400]
    return obs[:400]


def _build_cmmts(log: DGACAvionLog) -> str:
    return (log.cmmts or "")[:FCL_CMTS_MAX_LEN]


def _takeoff_landing_split(log: DGACAvionLog) -> dict[str, int]:
    """Split DGAC aggregate TO/LDG counts into day vs night buckets."""
    nbrto = log.nbrto or 0
    nbrla = log.nbrla or 0
    day_mins = _day_minutes(log)
    night_mins = _night_minutes(log)

    if night_mins > 0 and day_mins == 0:
        return {
            "take_off_day": 0,
            "take_off_night": nbrto,
            "landing_day": 0,
            "landing_night": nbrla,
        }
    return {
        "take_off_day": nbrto,
        "take_off_night": 0,
        "landing_day": nbrla,
        "landing_night": 0,
    }


def _name_pic(log: DGACAvionLog, role: str, cdb_mins: int) -> str:
    if role == ROLE_INST or role == ROLE_CDB or cdb_mins > 0:
        return "SELF"
    staff = _first_staff_name(log.staffob)
    return staff or "SELF"


def dgac_log_to_fcl_kwargs(log: DGACAvionLog) -> dict[str, Any]:
    """
    Map a DGACAvionLog instance to keyword arguments for FCL1080Log creation.

    Instructor flights (fctbrd Inst) put all flight time in pilot_time_inst only,
    so Cloudy FCL totals do not double-count PIC and instructor hours.
    """
    role = normalize_fctbrd(log.fctbrd)
    mono_mins = _mono_minutes(log)
    mul_mins = _mul_minutes(log)
    total = _flight_total_minutes(log)
    day_mins = _day_minutes(log)
    night_mins = _night_minutes(log)
    cdb_mins = _cdb_minutes(log)
    dual_mins = _dual_minutes(log)
    cop_mins = _copilot_minutes(log)
    departure_time, arrival_time = parse_obs_times(log.obs or "")
    to_ldg = _takeoff_landing_split(log)

    if role == ROLE_INST:
        pilot_time_in_cmd = 0
        pilot_time_dual = 0
        pilot_timpe_cop = 0
        pilot_time_inst = total
    else:
        pilot_time_in_cmd = cdb_mins
        pilot_time_dual = dual_mins
        pilot_timpe_cop = cop_mins
        pilot_time_inst = 0

    single_pilot_se = mono_mins > 0
    single_pilot_me = mul_mins > 0
    # DGAC multimoteurs = multi-engine, not multi-pilot crew.
    single_pilot_time = total if (single_pilot_se or single_pilot_me) else 0
    multi_pilot_time = 0

    kwargs: dict[str, Any] = {
        "date": log.date,
        "cdate": log.cdate,
        "update": log.update,
        "visbl": log.visbl,
        "deleted": log.deleted,
        "optional_filter": log.optional_filter or "",
        "airpdep": icao_from_place(log.airpdep or ""),
        "airpar": icao_from_place(log.airpar or ""),
        "departure_place": icao_from_place(log.airpdep or ""),
        "departure_time": departure_time,
        "arrival_place": icao_from_place(log.airpar or ""),
        "arrival_time": arrival_time,
        "aircraft_type": log.aeronef_type or "",
        "aircraft_imma": log.aeronef_imma or "",
        "single_pilot_se": single_pilot_se,
        "single_pilot_me": single_pilot_me,
        "single_pilot_time": single_pilot_time,
        "multi_pilot_time": multi_pilot_time,
        "total_time_flight": total,
        "name_pic": _name_pic(log, role, cdb_mins if role != ROLE_INST else 0),
        "take_off_day": to_ldg["take_off_day"],
        "take_off_night": to_ldg["take_off_night"],
        "landing_day": to_ldg["landing_day"],
        "landing_night": to_ldg["landing_night"],
        "op_time_night": night_mins,
        "op_time_ifr": (log.vai_dbl or 0) + (log.vai_plt or 0),
        "pilot_time_in_cmd": pilot_time_in_cmd,
        "pilot_timpe_cop": pilot_timpe_cop,
        "pilot_time_dual": pilot_time_dual,
        "pilot_time_inst": pilot_time_inst,
        "obs": _build_remarks(log),
        "cmmts": _build_cmmts(log),
        "staffob": log.staffob or "",
        "synthetic_date": None,
        "synthetic_type": "",
        "synthetic_time": 0,
    }

    simu = log.simu or 0
    if simu > 0 and total == 0:
        kwargs["synthetic_date"] = log.date
        kwargs["synthetic_type"] = "Simulator"
        kwargs["synthetic_time"] = simu
        kwargs["total_time_flight"] = simu

    return kwargs


def summarize_fcl_kwargs(kwargs_list: list[dict[str, Any]]) -> dict[str, int]:
    """Aggregate minute totals from converted kwargs (for dry-run reporting)."""
    keys = (
        "total_time_flight",
        "pilot_time_in_cmd",
        "pilot_timpe_cop",
        "pilot_time_dual",
        "pilot_time_inst",
        "op_time_night",
        "op_time_ifr",
        "synthetic_time",
    )
    totals = {key: 0 for key in keys}
    for kwargs in kwargs_list:
        for key in keys:
            totals[key] += kwargs.get(key) or 0
    return totals
