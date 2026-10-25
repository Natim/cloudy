from django.contrib.auth.models import User
from ninja.errors import HttpError

from cloudy.logbooks.models import LogBookBase

from .serialization import logbook_to_dict

__all__ = ["get_owned_logbook", "logbook_to_dict"]


def get_owned_logbook(user: User, logbook_id: int) -> LogBookBase:
    try:
        logbook = LogBookBase.get_by_id(logbook_id)
    except LogBookBase.DoesNotExist as exc:
        raise HttpError(404, "Logbook not found") from exc
    if logbook is None or logbook.deleted or logbook.ownr_id != user.id:
        raise HttpError(404, "Logbook not found")
    return logbook
