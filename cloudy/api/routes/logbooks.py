from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError

from cloudy.logbooks import settings as book_settings
from cloudy.logbooks.forms import EditLbookNameForm
from cloudy.logbooks.models import LogBookBase

from ..auth import require_user
from ..logbooks_access import get_owned_logbook, logbook_to_dict
from ..schemas.logbooks import LogbookCreateIn, LogbookPatchIn
from ._common import bearer_auth

router = Router(tags=["logbooks"])


@router.get("/logbooks", response=list[dict], auth=bearer_auth)
def list_logbooks(request: HttpRequest):
    user = require_user(request)
    books = LogBookBase.active_for_user(user.pk)
    return [logbook_to_dict(b) for b in books]


@router.post("/logbooks", response={201: dict, 402: dict}, auth=bearer_auth)
def create_logbook(request: HttpRequest, payload: LogbookCreateIn):
    user = require_user(request)
    cat = payload.category
    if cat not in book_settings.MAP:
        raise HttpError(400, "Unknown logbook category")
    if not user.userprofile.has_payed_plan() and (len(user.userprofile.active_logbooks()) + 1) > 1:
        raise HttpError(402, "First Class plan required for additional logbooks")

    logbook_class = book_settings.MAP[cat]
    default_name = settings.LOG_BOOKS_NAME_MAP.get(cat, cat)
    name = payload.name or default_name
    name = LogBookBase.check_unique_name(log_book_class=logbook_class, user_id=user.id, name=name)
    book = logbook_class(name=name, ownr=user, cdate=datetime.now(), cat=cat)
    try:
        book.save()
    except ValidationError as exc:
        raise HttpError(400, str(exc)) from exc
    return 201, logbook_to_dict(book)


@router.get("/logbooks/{logbook_id}", response=dict, auth=bearer_auth)
def get_logbook(request: HttpRequest, logbook_id: int):
    user = require_user(request)
    return logbook_to_dict(get_owned_logbook(user, logbook_id))


@router.patch("/logbooks/{logbook_id}", response=dict, auth=bearer_auth)
def patch_logbook(request: HttpRequest, logbook_id: int, payload: LogbookPatchIn):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    if payload.name is not None:
        form = EditLbookNameForm(
            {"name": payload.name, "time_format": logbook.time_format, "height_format": logbook.height_format}
        )
        if not form.is_valid():
            raise HttpError(400, form.errors.as_json())
        form.rename(logbook, user.id)
    if payload.time_format is not None:
        logbook.time_format = payload.time_format
    if payload.height_format is not None and logbook.can_fly:
        logbook.height_format = payload.height_format
    logbook.save()
    return logbook_to_dict(logbook)
