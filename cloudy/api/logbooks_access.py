from __future__ import annotations

from django.contrib.auth.models import User
from ninja.errors import HttpError

from cloudy.logbooks.models import LogBookBase


def get_owned_logbook(user: User, logbook_id: int) -> LogBookBase:
    try:
        logbook = LogBookBase.get_by_id(logbook_id)
    except LogBookBase.DoesNotExist as exc:
        raise HttpError(404, "Logbook not found") from exc
    if logbook is None or logbook.deleted or logbook.ownr_id != user.id:
        raise HttpError(404, "Logbook not found")
    return logbook


def logbook_to_dict(logbook: LogBookBase) -> dict:
    return {
        "id": logbook.id,
        "name": logbook.name,
        "cat": logbook.cat,
        "time_format": logbook.time_format,
        "height_format": logbook.height_format,
        "cdate": logbook.cdate.isoformat(),
        "update": logbook.update.isoformat(),
        "visbl": logbook.visbl,
        "deleted": logbook.deleted,
    }
