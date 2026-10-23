from __future__ import annotations

from datetime import datetime

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from ninja import Body, File, Router, UploadedFile
from ninja.errors import HttpError
from ninja.pagination import paginate

from cloudy.aircrafts.models import Aircraft
from cloudy.core.models import FileModel
from cloudy.logbooks import settings as book_settings
from cloudy.logbooks.forms import EditLbookNameForm
from cloudy.logbooks.models import LogBase, LogBookBase

from .auth import issue_access_token, JwtBearer, require_user
from .form_data import save_log_from_api
from .logbooks_access import get_owned_logbook, logbook_to_dict
from .schemas import AircraftIn, LogbookCreateIn, LogbookPatchIn, TokenIn, TokenOut

router = Router()
auth = JwtBearer()


@router.post("/auth/token", response=TokenOut, auth=None)
def auth_token(request: HttpRequest, payload: TokenIn):
    user = authenticate(request=None, username=payload.email, password=payload.password)
    if user is None:
        raise HttpError(401, "Invalid credentials")
    access_token, expires_in = issue_access_token(user)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user_id": user.pk,
    }


@router.get("/logbooks", response=list[dict], auth=auth)
def list_logbooks(request: HttpRequest):
    user = require_user(request)
    books = LogBookBase.active_for_user(user.pk)
    return [logbook_to_dict(b) for b in books]


@router.post("/logbooks", response={201: dict, 402: dict}, auth=auth)
def create_logbook(request: HttpRequest, payload: LogbookCreateIn):
    user = require_user(request)
    cat = payload.cat
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


@router.get("/logbooks/{logbook_id}", response=dict, auth=auth)
def get_logbook(request: HttpRequest, logbook_id: int):
    user = require_user(request)
    return logbook_to_dict(get_owned_logbook(user, logbook_id))


@router.patch("/logbooks/{logbook_id}", response=dict, auth=auth)
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


@router.get("/logbooks/{logbook_id}/logs", response=list[dict], auth=auth)
@paginate
def list_logs(
    request: HttpRequest,
    logbook_id: int,
    date_from: str | None = None,
    date_to: str | None = None,
):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    start = datetime.fromisoformat(date_from) if date_from else None
    end = datetime.fromisoformat(date_to) if date_to else None
    qs = logbook.logs_qs(time_slice=(start, end))
    return [log._cast().to_json(serialize=False) for log in qs.order_by("-date")]


@router.get("/logbooks/{logbook_id}/logs/{log_id}", response=dict, auth=auth)
def get_log(request: HttpRequest, logbook_id: int, log_id: int):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    log = LogBase.get_by_id(log_id)
    if log is None or log.lbook_id != logbook.id or log.deleted:
        raise HttpError(404, "Log not found")
    return log._cast().to_json(serialize=False)


@router.post("/logbooks/{logbook_id}/logs", response={201: dict}, auth=auth)
def create_log(request: HttpRequest, logbook_id: int, payload: dict = Body(...)):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    try:
        log = save_log_from_api(user, logbook, payload)
    except ValueError as exc:
        raise HttpError(400, str(exc)) from exc
    return 201, log._cast().to_json(serialize=False)


@router.put("/logbooks/{logbook_id}/logs/{log_id}", response=dict, auth=auth)
def update_log(request: HttpRequest, logbook_id: int, log_id: int, payload: dict = Body(...)):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    log = LogBase.get_by_id(log_id)
    if log is None or log.lbook_id != logbook.id or log.deleted:
        raise HttpError(404, "Log not found")
    try:
        log = save_log_from_api(user, logbook, payload, log=log._cast())
    except ValueError as exc:
        raise HttpError(400, str(exc)) from exc
    return log._cast().to_json(serialize=False)


@router.delete("/logbooks/{logbook_id}/logs/{log_id}", response={204: None}, auth=auth)
def delete_log(request: HttpRequest, logbook_id: int, log_id: int):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    log = LogBase.get_by_id(log_id)
    if log is None or log.lbook_id != logbook.id:
        raise HttpError(404, "Log not found")
    log.deleted = True
    log.save()
    return 204, None


@router.get("/logbooks/{logbook_id}/reports", response=dict, auth=auth)
def get_reports(request: HttpRequest, logbook_id: int):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    return logbook.reports or {}


@router.put("/logbooks/{logbook_id}/reports", response=dict, auth=auth)
def put_reports(request: HttpRequest, logbook_id: int, payload: dict = Body(...)):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    form_class = logbook._report_form_model()
    reportform = form_class(logbook, payload)
    if not reportform.is_valid():
        raise HttpError(400, reportform.errors.as_json())
    logbook.reports = reportform.cleaned_data
    logbook.save()
    return logbook.reports


@router.get("/logbooks/{logbook_id}/aircraft", response=list[dict], auth=auth)
def list_aircraft(request: HttpRequest, logbook_id: int):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    return [
        {
            "id": a.id,
            "imma": a.imma,
            "type": a.type,
            "airport": a.airport,
            "photo_url": a.get_photo().url if a.get_photo() else None,
        }
        for a in Aircraft.objects.filter(logbook=logbook)
    ]


@router.post("/logbooks/{logbook_id}/aircraft", response={201: dict}, auth=auth)
def create_aircraft(request: HttpRequest, logbook_id: int, payload: AircraftIn):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    aircraft = Aircraft(logbook=logbook, imma=payload.imma, type=payload.type, airport=payload.airport)
    try:
        aircraft.full_clean()
        aircraft.save()
    except ValidationError as exc:
        raise HttpError(400, str(exc)) from exc
    return 201, {"id": aircraft.id, "imma": aircraft.imma, "type": aircraft.type, "airport": aircraft.airport}


@router.patch("/logbooks/{logbook_id}/aircraft/{aircraft_id}", response=dict, auth=auth)
def patch_aircraft(request: HttpRequest, logbook_id: int, aircraft_id: int, payload: AircraftIn):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    try:
        aircraft = Aircraft.objects.get(pk=aircraft_id, logbook=logbook)
    except Aircraft.DoesNotExist as exc:
        raise HttpError(404, "Aircraft not found") from exc
    aircraft.imma = payload.imma
    aircraft.type = payload.type
    aircraft.airport = payload.airport
    try:
        aircraft.full_clean()
        aircraft.save()
    except ValidationError as exc:
        raise HttpError(400, str(exc)) from exc
    return {"id": aircraft.id, "imma": aircraft.imma, "type": aircraft.type, "airport": aircraft.airport}


@router.delete("/logbooks/{logbook_id}/aircraft/{aircraft_id}", response={204: None}, auth=auth)
def delete_aircraft(request: HttpRequest, logbook_id: int, aircraft_id: int):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    deleted, _ = Aircraft.objects.filter(pk=aircraft_id, logbook=logbook).delete()
    if not deleted:
        raise HttpError(404, "Aircraft not found")
    return 204, None


@router.post("/logbooks/{logbook_id}/aircraft/{aircraft_id}/photo", response=dict, auth=auth)
def upload_aircraft_photo(
    request: HttpRequest,
    logbook_id: int,
    aircraft_id: int,
    file: UploadedFile = File(...),
):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    if not user.userprofile.can_upload_media():
        raise HttpError(402, "Insufficient storage quota")
    try:
        aircraft = Aircraft.objects.get(pk=aircraft_id, logbook=logbook)
    except Aircraft.DoesNotExist as exc:
        raise HttpError(404, "Aircraft not found") from exc
    fobject = FileModel(owner=user, file=file)
    fobject.save()
    aircraft.pictures.add(fobject)
    return {"url": fobject.file.url}


@router.post("/logbooks/{logbook_id}/logs/{log_id}/files", response=dict, auth=auth)
def upload_log_file(
    request: HttpRequest,
    logbook_id: int,
    log_id: int,
    file: UploadedFile = File(...),
):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    if not user.userprofile.can_upload_media():
        raise HttpError(402, "Insufficient storage quota")
    log = LogBase.get_by_id(log_id)
    if log is None or log.lbook_id != logbook.id or log.deleted:
        raise HttpError(404, "Log not found")
    fobject = FileModel(owner=user, file=file)
    fobject.save()
    log.files.add(fobject)
    return {"path": fobject.file.url}


@router.delete("/logbooks/{logbook_id}/logs/{log_id}/files/{file_id}", response={204: None}, auth=auth)
def delete_log_file(request: HttpRequest, logbook_id: int, log_id: int, file_id: int):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    log = LogBase.get_by_id(log_id)
    if log is None or log.lbook_id != logbook.id:
        raise HttpError(404, "Log not found")
    try:
        fobject = log.files.get(pk=file_id, owner=user, deleted=False)
    except FileModel.DoesNotExist as exc:
        raise HttpError(404, "File not found") from exc
    log.files.remove(fobject)
    fobject.deleted = True
    fobject.save()
    return 204, None
