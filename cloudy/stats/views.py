"""
Statistics views
----------------

These views are designed to be generic enough to support any kind of logbook.
Due to mongoengine's dumb way of storing objects (one mongo collection per
object type), we need to have the logbook_type in the URL.
Another solution would be to create a "bridge" collection which binds UIDs and
collections, but it would be a mess.
We can also create a single model, generic enough to support any kind of
logbook.
"""

# System imports {{{
import json
from datetime import datetime, timedelta

# }}}
# Third-party apps {{{
from dateutil.parser import parse as parse_dateutil
from django.conf import settings
from django.db.models import Q
from django.http import Http404, HttpResponse

# }}}
# Django imports {{{
from django.views.decorators.http import require_GET
from redis import Redis

from cloudy.core.utils import time_slice_to_string, traversal
from cloudy.logbooks.models import LogBookBase

# }}}
# Cloudy {{{
from cloudy.stats.models import Airport

# }}}


# Data {{{
END_DAY_TIME = {"hour": 23, "minute": 59, "second": 59, "microsecond": 999999}
# }}}


def place_field_names(logbook):
    if getattr(logbook, "cat", "") == "plane_fcl1080":
        return "departure_place", "arrival_place"
    return "airpdep", "airpar"


def airport_for_place(elem):
    """Match a log place string (ICAO, ``ICAO NAME``, or ``ICAO - Name``) to an Airport."""
    elem = (elem or "").strip()
    if not elem:
        return None
    airport = Airport.objects.filter(icao__iexact=elem).first()
    if airport:
        return airport
    if " - " in elem:
        icao, name = elem.split(" - ", 1)
        icao = icao.strip()
        name = name.strip()
    else:
        parts = elem.split()
        icao = parts[0]
        name = " ".join(parts[1:])
    qs = Airport.objects.filter(icao__iexact=icao)
    if name:
        named = qs.filter(airport__iexact=name).first()
        if named:
            return named
    return qs.first()


# CONSTANCE_CONNECTION was the pre-2.0 django-constance setting name; the current
# release reads CONSTANCE_REDIS_CONNECTION, which settings.py defines.
redis = Redis(**settings.CONSTANCE_REDIS_CONNECTION)


@require_GET
def airports(request, maximum=5):
    """
    Dirty function to compute the grading of the airports.
    FIXME: Should be merged in the stats module.


    {
        begin_date: 'YYYY/MM/DD',
        end_date: 'YYYY/MM/DD',
        logbook_id: '44564645651161',
        logbook_type: 'avion'
    }
    """

    # Convert the request payload to a pythonic object
    request_payload = json.loads(request.GET["payload"])

    # Grab the logbook we are dealing with according to the request types
    actual_logbook = LogBookBase.get_by_id(request_payload["logbook_id"])

    if actual_logbook == None:
        raise Http404

    # Compute the string representation of the time_slice because totals are
    # indexed by repr of time_slice and filters in database.
    first = (
        None
        if request_payload["begin_date"] in ["none", ""]
        else parse_dateutil(request_payload["begin_date"], dayfirst=True)
    )
    last = (
        None
        if request_payload["end_date"] in ["none", ""]
        else parse_dateutil(request_payload["end_date"], dayfirst=True)
    )
    # last date include the whole day so we stretch the range
    if last:
        last = datetime(day=last.day, month=last.month, year=last.year, **END_DAY_TIME)

    time_slice = (first, last)
    logs = actual_logbook.logs_qs(time_slice)
    results = {}

    key_dep = "airpdep"
    key_arr = "airpar"
    if actual_logbook.cat == "plane_fcl1080":
        key_dep = "departure_place"
        key_arr = "arrival_place"
    for log in logs:
        airport_dep = getattr(log, key_dep)
        airport_ar = getattr(log, key_arr)
        results[airport_ar] = results.get(airport_ar, 0) + 1
        results[airport_dep] = results.get(airport_dep, 0) + 1

    # Remove flights without airports FIXME should be done in the mongo query
    if "" in results.keys():
        del results[""]

    # Now sort airports
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)[0:maximum]

    # Return the data using JSON
    return HttpResponse(json.dumps(sorted_results))


@require_GET
def map_places(request):
    request_payload = json.loads(request.GET["payload"])

    actual_logbook = LogBookBase.get_by_id(request_payload["logbook_id"])

    if actual_logbook is None:
        raise Http404

    first = (
        None
        if request_payload["begin_date"] in ["none", ""]
        else parse_dateutil(request_payload["begin_date"], dayfirst=True)
    )
    last = (
        None
        if request_payload["end_date"] in ["none", ""]
        else parse_dateutil(request_payload["end_date"], dayfirst=True)
    )
    if last:
        last = datetime(day=last.day, month=last.month, year=last.year, **END_DAY_TIME)

    time_slice = (first, last)

    if settings.CACHING:
        key_values = {"logbook_id": actual_logbook.id, "str_timeslice": time_slice_to_string(time_slice)}
        key = "map:%(logbook_id)s:%(str_timeslice)s" % key_values
        cached_result = redis.get(key)
        if cached_result is not None:
            if isinstance(cached_result, bytes):
                cached_result = cached_result.decode()
            return HttpResponse(cached_result, content_type="application/json")

    dep, arr = place_field_names(actual_logbook)
    query_with_airport = ~Q(**{f"{dep}__exact": "", f"{arr}__exact": ""})
    logs = actual_logbook.logs_qs(time_slice, qs=[query_with_airport]).values_list(dep, arr)

    data = []
    seen = set()
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

    output = json.dumps(data)

    if settings.CACHING:
        key_values = {"logbook_id": actual_logbook.id, "str_timeslice": time_slice_to_string(time_slice)}
        key = "map:%(logbook_id)s:%(str_timeslice)s" % key_values
        redis.set(key, output)

    return HttpResponse(output, content_type="application/json")


@require_GET
def count_foo(request, max_res=None):
    # Convert the request payload to a Python object
    request_payload = json.loads(request.GET["payload"])

    # Grab the logbook we are dealing with
    actual_logbook = LogBookBase.get_by_id(request_payload["logbook_id"])

    if actual_logbook == None:
        raise Http404

    # Compute the string representation of the time_slice because totals are
    # indexed by repr of time_slice and filters in database.
    first = (
        None
        if request_payload["begin_date"] in ["none", ""]
        else parse_dateutil(request_payload["begin_date"], dayfirst=True)
    )
    last = (
        None
        if request_payload["end_date"] in ["none", ""]
        else parse_dateutil(request_payload["end_date"], dayfirst=True)
    )
    # last date include the whole day so we stretch the range
    if last:
        last = datetime(day=last.day, month=last.month, year=last.year, **END_DAY_TIME)

    # Check that total & group_by keys are presend in payload
    request_totals = request_payload.get("total", None)
    request_groupby = request_payload.get("group_by", None)
    max_res = request_payload.get("max", max_res)

    if not request_totals or not request_groupby:
        return HttpResponse(json.dumps({"success": False, "msg": "wrong params"}))

    time_slice = (first, last)
    res = actual_logbook.get_totals([request_totals], time_slice, group_by=request_groupby, reports=False)
    data = res[request_totals]
    del data["__sum__"]
    couples = zip(data.keys(), data.values())
    sorted_results = sorted(couples, key=lambda x: x[1], reverse=True)
    if max_res:
        sorted_results = sorted_results[0:max_res]

    return HttpResponse(json.dumps(sorted_results))


@require_GET
def get_choices(request):
    """
    Get the choices for certain data. Used to fill choices lists.
    JSON payload in GET['payload']:

    {
        logbook_id: '44564645651161',
        logbook_type: 'avion',
        fields: ['field.1.2', 'field.12']
    }
    """

    # Convert the request payload to a pythonic object
    request_payload = json.loads(request.GET["payload"])

    # Grab the logbook we are dealing with according to the request types
    actual_logbook = LogBookBase.get_by_id(request_payload["logbook_id"])

    if actual_logbook == None:
        raise Http404

    # Compute the string representation of the time_slice because totals are
    # indexed by repr of time_slice and filters in database.
    first = (
        None
        if request_payload["begin_date"] in ["none", ""]
        else parse_dateutil(request_payload["begin_date"], dayfirst=True)
    )
    last = (
        None
        if request_payload["end_date"] in ["none", ""]
        else parse_dateutil(request_payload["end_date"], dayfirst=True)
    )

    # last date include the whole day so we stretch the range
    if last:
        last = datetime(day=last.day, month=last.month, year=last.year, **END_DAY_TIME)

    time_slice = (first, last)

    logs = actual_logbook.logs_qs(time_slice)

    fields = request_payload["fields"]
    results = {}
    for key in fields:
        results[key] = []

    for log in logs:
        for field in fields:
            data = traversal(log, field.replace("__", "."))
            if data not in results[field]:
                if not data == "":
                    results[field].append(data)

    return HttpResponse(json.dumps(results))


@require_GET
def graphs_data(request):
    """
    View which returns data for stats graphs. It only accepts GET request with
    the following JSON payload (obviously stored in GET['payload']):

    {
        begin_date: 'YYYY/MM/DD',
        end_date: 'YYYY/MM/DD',
        total: 'total_name' || total: ['list', 'of', 'totals'],
        logbook_id: '44564645651161',
        logbook_type: 'avion'

        group_by: 'aeronef.type', (optional, should match rules groupbyes)
        filters: {      (optional, keys should match field names)
                    'aeronef.type': 'foo',
                    'function': 'copilot'
                 }
    }

    If you want to use pie charts, you *must* use group_by.
    """
    # Convert the request payload to a pythonic object
    request_payload = json.loads(request.GET["payload"])

    # Grab the logbook we are dealing with according to the request types
    actual_logbook = LogBookBase.get_by_id(request_payload["logbook_id"])

    if actual_logbook == None:
        raise Http404

    # Compute the string representation of the time_slice because totals are
    # indexed by repr of time_slice and filters in database.
    first = (
        None
        if request_payload["begin_date"] in ["none", ""]
        else parse_dateutil(request_payload["begin_date"], dayfirst=True)
    )
    last = (
        None
        if request_payload["end_date"] in ["none", ""]
        else parse_dateutil(request_payload["end_date"], dayfirst=True)
    )

    # last date include the whole day so we stretch the range
    if last:
        last = datetime(day=last.day, month=last.month, year=last.year, **END_DAY_TIME)

    if request.GET.get("select", "") == "lifetime":
        first = None

    time_slice = (first, last)

    filters = request_payload.get("filters", {})
    group_by = request_payload.get("group_by", None)

    # Case one: multiple totals => pie chart
    if request_payload["total"].__class__ == list:
        # So we want totals, probably for pie charts
        # TODO stop ignoring `filters` and `group_by`
        results = []
        values = {}

        # Grab the values of requested totals
        for total in request_payload["total"]:
            # Grab the total
            values[total] = actual_logbook.get_totals([total], time_slice)[total]

        # Create returned data
        for total, value in values.items():
            results.append({"label": total, "data": value})

        # Finally returns the JSON converted results
        return HttpResponse(json.dumps(results))

    else:
        # So we have a multi-requests payload. Therefore we must compute time
        # slices of each request based on the following idea:
        #
        # If the difference between the original two dates is more than
        #   5 years -> we split by year
        #   1 year -> we split by month
        #   2 months -> we split by week
        #   less than two months -> we split by day
        #
        # This seems to be a reasonable algorithm, though it is easily
        # tweakable by changing values of the conditional ifs below.

        # first = time_slice[0]
        # last = time_slice[1]

        # If we don't have a start date, we use the oldest / youngest log entries
        if first == None:
            first_log = actual_logbook.logs_qs()
            if len(first_log) < 1:
                first_log = None
            else:
                first_log = first_log[0]
            if first_log == None:
                return HttpResponse(json.dumps([]))
            first = datetime.fromordinal(first_log.date.date().toordinal())
        if last == None:
            last = datetime.fromordinal(datetime.now().date().toordinal())

        # In case we dont group we change the spreading rules
        # as we have more space
        if group_by == None:
            slots = smart_date_slotifier(first, last, rules=[26, 30, 30, 65, 30])
        else:
            slots = smart_date_slotifier(first, last)

        # Prepare the encapsulation
        encapsulated_results = {"slices_name": slots["slices_name"], "data": []}
        # Now we have to compute each of these results *sigh* that *should* be
        # improved.

        if group_by == None:
            totals_results = []
            total_group_by_key = request_payload["total"]
            for range_slice in slots["slices_range"]:
                loctotals = actual_logbook.get_totals(
                    [total_group_by_key], range_slice, filters, reports=False
                )
                totals_results.append(loctotals[total_group_by_key])

            encapsulated_results["data"] = [
                {
                    "group_key": request_payload["total"],
                    "data": totals_results,
                }
            ]
            encapsulated_results["total"] = sum(totals_results)

        else:
            totals_results = {}
            res_list = []
            # first pass create the keys and copy results in res_list
            for range_slice in slots["slices_range"]:
                res = actual_logbook.get_totals([request_payload["total"]], range_slice, filters, group_by)
                res = res[request_payload["total"]]
                res_list.append(res)
                for key, value in res.items():
                    if key not in totals_results.keys():
                        totals_results[key] = []

            # loop again slices result to populate values
            for i, _ in enumerate(slots["slices_range"]):
                for key, _ in totals_results.items():
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
            # sort to get top 5 higher value list
            sorted_slices = sorted(encapsulated_results["data"], key=lambda k: sum(k["data"]), reverse=True)
            encapsulated_results["data"] = sorted_slices[:5]
            # Finally, push the data out

        return HttpResponse(json.dumps(encapsulated_results))


import calendar

from dateutil import rrule


def smart_date_slotifier(first, last, rules=[26, 8, 8, 22, 8]):
    """
    Given a startdate / enddate it returns a dic with the following form:
    {
        'slices_name': ['Sun 12', 'Mon 13', 'Tue 14'],
        'slices_range': [(d1,d2), ...]
    }
    Starting date of first slot should be the real first date.
    When we create monthly slot for example we will have
    15 jan - 31 jan, 1 fev - end fev, 1 mars-end mars.
    """
    # sanity check, I happened to have last < first after an import :/
    if last < first:
        first, last = last, first

    diff = last - first
    data = {"slices_name": [], "slices_range": []}

    year_rrule = rrule.rrule(rrule.YEARLY, dtstart=first, until=last)
    month_rrule = rrule.rrule(rrule.MONTHLY, dtstart=first, until=last)
    nbr_month = len(list(month_rrule))
    nbr_year = len(list(year_rrule))
    # tracking special case for the first slice
    is_first_slice_done = False
    # first slice insert needs to start from star
    # > 8 years

    if nbr_month > rules[0]:
        my_year_interval = nbr_year // rules[1] + 1
        rst = rrule.rrule(rrule.YEARLY, interval=my_year_interval + 1, dtstart=first, until=last)
        for dt in rst:
            vday = 1
            vmonth = 1
            if not is_first_slice_done:
                vday = dt.day
                vmonth = dt.month
                is_first_slice_done = True
            slice_start_date = datetime(day=vday, month=vmonth, year=dt.year)
            slice_end_date = datetime(day=31, month=12, year=dt.year + my_year_interval, **END_DAY_TIME)
            slc_name = "{}-{}".format(dt.strftime("%Y"), slice_end_date.strftime("%Y"))
            data["slices_name"].append(slc_name)
            data["slices_range"].append((slice_start_date, slice_end_date))

    # > 8 months: bi monthly
    elif nbr_month > rules[2]:
        for dt in rrule.rrule(rrule.MONTHLY, interval=2, dtstart=first, until=last):
            data["slices_name"].append(dt.strftime("%b %Y"))
            vday = 1
            if not is_first_slice_done:
                vday = dt.day
                is_first_slice_done = True
            slice_start_date = datetime(day=vday, month=dt.month, year=dt.year)
            # get end of next month
            next_month = dt + timedelta(days=31)
            _, nbr_days = calendar.monthrange(next_month.year, next_month.month)
            slice_end_date = datetime(
                day=nbr_days, month=next_month.month, year=next_month.year, **END_DAY_TIME
            )
            data["slices_range"].append((slice_start_date, slice_end_date))
    # monthly
    elif diff.days > rules[3]:
        for dt in month_rrule:
            data["slices_name"].append(dt.strftime("%b %Y"))
            vday = 1
            if not is_first_slice_done:
                vday = dt.day
                is_first_slice_done = True
            slice_start_date = datetime(day=vday, month=dt.month, year=dt.year)
            # get end of month
            _, nbr_days = calendar.monthrange(dt.year, dt.month)
            slice_end_date = datetime(day=nbr_days, month=dt.month, year=dt.year, **END_DAY_TIME)
            data["slices_range"].append((slice_start_date, slice_end_date))
    # > than 8 days: bi daily
    elif diff.days > rules[4]:
        for dt in rrule.rrule(rrule.DAILY, interval=2, dtstart=first, until=last):
            slice_start_date = dt
            slice_end_date = dt + timedelta(days=1)
            slice_end_date = datetime(
                day=slice_end_date.day, month=slice_end_date.month, year=slice_end_date.year, **END_DAY_TIME
            )
            data["slices_range"].append((slice_start_date, slice_end_date))
            data["slices_name"].append(dt.strftime("%a %d"))
    # < 8 days
    else:
        # Stats from monday 2 to tuesday 3 will include tuesday.
        # Monday 2 00:00 to wednesday 4 00:00

        for dt in rrule.rrule(rrule.DAILY, dtstart=first, until=last):
            slice_start_date = dt
            slice_end_date = datetime(day=dt.day, month=dt.month, year=dt.year, **END_DAY_TIME)
            data["slices_range"].append((slice_start_date, slice_end_date))
            data["slices_name"].append(dt.strftime("%a %d"))

    return data
