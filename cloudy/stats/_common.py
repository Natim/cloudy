"""Helpers shared by stats views and service layer."""

import calendar
from datetime import datetime, timedelta

from dateutil import rrule

from cloudy.stats.models import Airport

END_DAY_TIME = {"hour": 23, "minute": 59, "second": 59, "microsecond": 999999}


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


def smart_date_slotifier(first, last, rules=(26, 8, 8, 22, 8)):
    if last < first:
        first, last = last, first

    diff = last - first
    data = {"slices_name": [], "slices_range": []}

    year_rrule = rrule.rrule(rrule.YEARLY, dtstart=first, until=last)
    month_rrule = rrule.rrule(rrule.MONTHLY, dtstart=first, until=last)
    nbr_month = len(list(month_rrule))
    nbr_year = len(list(year_rrule))
    is_first_slice_done = False

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

    elif nbr_month > rules[2]:
        for dt in rrule.rrule(rrule.MONTHLY, interval=2, dtstart=first, until=last):
            data["slices_name"].append(dt.strftime("%b %Y"))
            vday = 1
            if not is_first_slice_done:
                vday = dt.day
                is_first_slice_done = True
            slice_start_date = datetime(day=vday, month=dt.month, year=dt.year)
            next_month = dt + timedelta(days=31)
            _, nbr_days = calendar.monthrange(next_month.year, next_month.month)
            slice_end_date = datetime(
                day=nbr_days, month=next_month.month, year=next_month.year, **END_DAY_TIME
            )
            data["slices_range"].append((slice_start_date, slice_end_date))
    elif diff.days > rules[3]:
        for dt in month_rrule:
            data["slices_name"].append(dt.strftime("%b %Y"))
            vday = 1
            if not is_first_slice_done:
                vday = dt.day
                is_first_slice_done = True
            slice_start_date = datetime(day=vday, month=dt.month, year=dt.year)
            _, nbr_days = calendar.monthrange(dt.year, dt.month)
            slice_end_date = datetime(day=nbr_days, month=dt.month, year=dt.year, **END_DAY_TIME)
            data["slices_range"].append((slice_start_date, slice_end_date))
    elif diff.days > rules[4]:
        for dt in rrule.rrule(rrule.DAILY, interval=2, dtstart=first, until=last):
            slice_start_date = dt
            slice_end_date = dt + timedelta(days=1)
            slice_end_date = datetime(
                day=slice_end_date.day, month=slice_end_date.month, year=slice_end_date.year, **END_DAY_TIME
            )
            data["slices_range"].append((slice_start_date, slice_end_date))
            data["slices_name"].append(dt.strftime("%a %d"))
    else:
        for dt in rrule.rrule(rrule.DAILY, dtstart=first, until=last):
            slice_start_date = dt
            slice_end_date = datetime(day=dt.day, month=dt.month, year=dt.year, **END_DAY_TIME)
            data["slices_range"].append((slice_start_date, slice_end_date))
            data["slices_name"].append(dt.strftime("%a %d"))

    return data
