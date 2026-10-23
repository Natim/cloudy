"""MCP tools for pilot-scoped logbook data and statistics."""

from datetime import datetime
from typing import Any

from mcp.server.mcpserver import MCPServer

from cloudy.aircrafts.models import Aircraft
from cloudy.logbooks.models import LogBase, LogBookBase
from cloudy.stats import service
from cloudy.stats.service import LogbookAccessError

from .auth import get_api_user
from .logbooks_access import logbook_to_dict
from .serialization import aircraft_to_dict, log_to_api_dict

mcp = MCPServer("cloudy-logbook")


def _user():
    user = get_api_user()
    if user is None:
        raise LogbookAccessError("Missing API user context")
    return user


@mcp.tool()
def list_logbooks() -> list[dict[str, Any]]:
    """List logbooks owned by the authenticated pilot."""
    user = _user()
    return [logbook_to_dict(b) for b in LogBookBase.active_for_user(user.pk)]


@mcp.tool()
def get_logbook(logbook_id: int) -> dict[str, Any]:
    """Return one logbook by id (must belong to the authenticated pilot)."""
    user = _user()
    logbook = service.logbook_for_user(user, logbook_id)
    return logbook_to_dict(logbook)


@mcp.tool()
def list_aircraft(logbook_id: int) -> list[dict[str, Any]]:
    """List aircraft registered on a logbook."""
    user = _user()
    logbook = service.logbook_for_user(user, logbook_id)
    return [aircraft_to_dict(a) for a in Aircraft.objects.filter(logbook=logbook)]


@mcp.tool()
def list_logs(
    logbook_id: int,
    date_from: str = "",
    date_to: str = "",
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List logbook entries (newest first), with optional ISO date filters."""
    user = _user()
    logbook = service.logbook_for_user(user, logbook_id)
    start = datetime.fromisoformat(date_from) if date_from else None
    end = datetime.fromisoformat(date_to) if date_to else None
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    qs = logbook.logs_qs(time_slice=(start, end)).order_by("-date")
    page = qs[offset : offset + limit]
    return [log_to_api_dict(row._cast().to_json(serialize=False)) for row in page]


@mcp.tool()
def get_log(logbook_id: int, log_id: int) -> dict[str, Any]:
    """Return a single logbook entry by id."""
    user = _user()
    logbook = service.logbook_for_user(user, logbook_id)
    log = LogBase.get_by_id(log_id)
    if log is None or log.lbook_id != logbook.id or log.deleted:
        raise LogbookAccessError("Log not found")
    return log_to_api_dict(log._cast().to_json(serialize=False))


@mcp.tool()
def describe_totals(logbook_id: int) -> list[str]:
    """Return total metric names available for a logbook."""
    user = _user()
    logbook = service.logbook_for_user(user, logbook_id)
    return list(logbook.totals_rules().keys())


@mcp.tool()
def get_totals(
    logbook_id: int,
    total_names: list[str],
    begin_date: str = "",
    end_date: str = "",
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute named totals for a date range."""
    user = _user()
    payload = {
        "begin_date": begin_date,
        "end_date": end_date,
        "filters": filters or {},
    }
    return service.get_named_totals(user, logbook_id, total_names, payload)


@mcp.tool()
def time_series(
    logbook_id: int,
    total: str,
    begin_date: str = "",
    end_date: str = "",
    group_by: str | None = None,
    filters: dict[str, Any] | None = None,
    lifetime: bool = False,
) -> Any:
    """Return chart time-series data for one total."""
    user = _user()
    payload = {
        "begin_date": begin_date,
        "end_date": end_date,
        "total": total,
        "group_by": group_by,
        "filters": filters or {},
    }
    return service.graphs_data_payload(user, logbook_id, payload, lifetime=lifetime)


@mcp.tool()
def top_values(
    logbook_id: int,
    total: str,
    group_by: str,
    begin_date: str = "",
    end_date: str = "",
    max_results: int = 10,
) -> list[tuple[str, int | float]]:
    """Return top grouped values for a total (same as /graphs/count_foo/)."""
    user = _user()
    payload = {
        "begin_date": begin_date,
        "end_date": end_date,
        "total": total,
        "group_by": group_by,
        "max": max_results,
    }
    return service.top_grouped_totals(user, logbook_id, payload)


@mcp.tool()
def airports(
    logbook_id: int,
    begin_date: str = "",
    end_date: str = "",
    maximum: int = 5,
) -> dict[str, Any]:
    """Airport visit counts and map coordinates for a date range."""
    user = _user()
    payload = {"begin_date": begin_date, "end_date": end_date}
    counts = service.airport_counts(user, logbook_id, payload, maximum=maximum)
    points = service.map_places_data(user, logbook_id, payload)
    return {"counts": counts, "map_points": points}
