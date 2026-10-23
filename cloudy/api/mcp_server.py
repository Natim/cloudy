"""MCP tools for pilot-scoped logbook statistics."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from cloudy.logbooks.models import LogBookBase
from cloudy.stats import service
from cloudy.stats.service import LogbookAccessError

from .auth import get_api_user
from .logbooks_access import logbook_to_dict

mcp = MCPServer("cloudy-logbook-stats")


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
