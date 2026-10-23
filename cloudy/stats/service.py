"""Shared logbook statistics queries for web graphs, REST, and MCP."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from dateutil.parser import parse as parse_dateutil
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from redis import Redis

from cloudy.core.utils import time_slice_to_string, traversal
from cloudy.logbooks.models import LogBookBase

from ._common import airport_for_place, END_DAY_TIME, place_field_names, smart_date_slotifier

redis = Redis(**settings.CONSTANCE_REDIS_CONNECTION)


class LogbookAccessError(Exception):
    """Raised when the user may not access the logbook."""


def logbook_for_user(user: User, logbook_id: int) -> LogBookBase:
    try:
        logbook = LogBookBase.get_by_id(logbook_id)
    except LogBookBase.DoesNotExist as exc:
        raise LogbookAccessError from exc
    if logbook is None:
        raise LogbookAccessError
    if logbook.ownr_id != user.id:
        raise LogbookAccessError
    return logbook


def parse_time_slice(payload: dict[str, Any]) -> tuple[datetime | None, datetime | None]:
    first = (
        None
        if payload.get("begin_date") in (None, "none", "")
        else parse_dateutil(payload["begin_date"], dayfirst=True)
    )
    last = (
        None
        if payload.get("end_date") in (None, "none", "")
        else parse_dateutil(payload["end_date"], dayfirst=True)
    )
    if last:
        last = datetime(day=last.day, month=last.month, year=last.year, **END_DAY_TIME)
    return first, last


def airport_counts(
    user: User,
    logbook_id: int,
    payload: dict[str, Any],
    maximum: int = 5,
) -> list[tuple[str, int]]:
    logbook = logbook_for_user(user, logbook_id)
    first, last = parse_time_slice(payload)
    time_slice = (first, last)
    logs = logbook.logs_qs(time_slice)
    results: dict[str, int] = {}

    key_dep, key_arr = place_field_names(logbook)
    for log in logs:
        airport_dep = getattr(log, key_dep)
        airport_ar = getattr(log, key_arr)
        results[airport_ar] = results.get(airport_ar, 0) + 1
        results[airport_dep] = results.get(airport_dep, 0) + 1

    if "" in results:
        del results[""]

    return sorted(results.items(), key=lambda x: x[1], reverse=True)[:maximum]


def map_places_data(user: User, logbook_id: int, payload: dict[str, Any]) -> list[list[str]]:
    logbook = logbook_for_user(user, logbook_id)
    first, last = parse_time_slice(payload)
    time_slice = (first, last)

    if settings.CACHING:
        key_values = {"logbook_id": logbook.id, "str_timeslice": time_slice_to_string(time_slice)}
        key = "map:%(logbook_id)s:%(str_timeslice)s" % key_values
        cached_result = redis.get(key)
        if cached_result is not None:
            if isinstance(cached_result, bytes):
                cached_result = cached_result.decode()
            return json.loads(cached_result)

    dep, arr = place_field_names(logbook)
    query_with_airport = ~Q(**{f"{dep}__exact": "", f"{arr}__exact": ""})
    logs = logbook.logs_qs(time_slice, qs=[query_with_airport]).values_list(dep, arr)

    data: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for log in logs:
        for elem in log:
            airport = airport_for_place(elem)
            if airport is None:
                continue
            coords = airport.coordinates()
            key = tuple(coords)
            if key in seen:
                continue
            seen.add(key)
            data.append(coords)

    if settings.CACHING:
        key_values = {"logbook_id": logbook.id, "str_timeslice": time_slice_to_string(time_slice)}
        key = "map:%(logbook_id)s:%(str_timeslice)s" % key_values
        redis.set(key, json.dumps(data))

    return data


def top_grouped_totals(
    user: User,
    logbook_id: int,
    payload: dict[str, Any],
    max_res: int | None = None,
) -> list[tuple[str, int | float]]:
    logbook = logbook_for_user(user, logbook_id)
    first, last = parse_time_slice(payload)
    request_totals = payload.get("total")
    request_groupby = payload.get("group_by")
    max_res = payload.get("max", max_res)

    if not request_totals or not request_groupby:
        raise ValueError("wrong params")

    time_slice = (first, last)
    res = logbook.get_totals([request_totals], time_slice, group_by=request_groupby, reports=False)
    data = res[request_totals]
    del data["__sum__"]
    couples = zip(data.keys(), data.values(), strict=False)
    sorted_results = sorted(couples, key=lambda x: x[1], reverse=True)
    if max_res:
        sorted_results = sorted_results[:max_res]
    return sorted_results


def field_choices(
    user: User,
    logbook_id: int,
    payload: dict[str, Any],
) -> dict[str, list[Any]]:
    logbook = logbook_for_user(user, logbook_id)
    first, last = parse_time_slice(payload)
    time_slice = (first, last)
    logs = logbook.logs_qs(time_slice)

    fields = payload["fields"]
    results = {key: [] for key in fields}

    for log in logs:
        for field in fields:
            data = traversal(log, field.replace("__", "."))
            if data not in results[field] and data != "":
                results[field].append(data)

    return results


def graphs_data_payload(
    user: User,
    logbook_id: int,
    payload: dict[str, Any],
    *,
    lifetime: bool = False,
) -> Any:
    logbook = logbook_for_user(user, logbook_id)
    first, last = parse_time_slice(payload)

    if lifetime:
        first = None

    time_slice = (first, last)
    filters = payload.get("filters", {})
    group_by = payload.get("group_by")
    total = payload["total"]

    if isinstance(total, list):
        results = []
        values = {}
        for name in total:
            values[name] = logbook.get_totals([name], time_slice)[name]
        for name, value in values.items():
            results.append({"label": name, "data": value})
        return results

    if first is None:
        first_log = logbook.logs_qs()
        if len(first_log) < 1:
            return []
        first_log = first_log[0]
        first = datetime.fromordinal(first_log.date.date().toordinal())
    if last is None:
        last = datetime.fromordinal(datetime.now().date().toordinal())

    if group_by is None:
        slots = smart_date_slotifier(first, last, rules=[26, 30, 30, 65, 30])
    else:
        slots = smart_date_slotifier(first, last)

    encapsulated_results: dict[str, Any] = {"slices_name": slots["slices_name"], "data": []}

    if group_by is None:
        totals_results = []
        total_group_by_key = total
        for range_slice in slots["slices_range"]:
            loctotals = logbook.get_totals([total_group_by_key], range_slice, filters, reports=False)
            totals_results.append(loctotals[total_group_by_key])

        encapsulated_results["data"] = [
            {
                "group_key": total,
                "data": totals_results,
            }
        ]
        encapsulated_results["total"] = sum(totals_results)
    else:
        totals_results: dict[str, list] = {}
        res_list = []
        for range_slice in slots["slices_range"]:
            res = logbook.get_totals([total], range_slice, filters, group_by)
            res = res[total]
            res_list.append(res)
            for key in res:
                if key not in totals_results:
                    totals_results[key] = []

        for i, _ in enumerate(slots["slices_range"]):
            for key in totals_results:
                is_res_for_key = res_list[i].get(key, None)
                if is_res_for_key:
                    totals_results[key].append(res_list[i][key])
                else:
                    totals_results[key].append(0)

        del totals_results["__sum__"]
        for key, value in totals_results.items():
            encapsulated_results["data"].append(
                {
                    "label": key,
                    "data": value,
                }
            )
        sorted_slices = sorted(encapsulated_results["data"], key=lambda k: sum(k["data"]), reverse=True)
        encapsulated_results["data"] = sorted_slices[:5]

    return encapsulated_results


def get_named_totals(
    user: User,
    logbook_id: int,
    total_names: list[str],
    payload: dict[str, Any],
    *,
    reports: bool = True,
) -> dict[str, Any]:
    logbook = logbook_for_user(user, logbook_id)
    first, last = parse_time_slice(payload)
    filters = payload.get("filters", {})
    group_by = payload.get("group_by")
    return logbook.get_totals(total_names, (first, last), filters=filters, group_by=group_by, reports=reports)
