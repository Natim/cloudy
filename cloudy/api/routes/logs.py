from datetime import datetime

from django.http import HttpRequest
from ninja import Body, File, Router, UploadedFile
from ninja.errors import HttpError
from ninja.pagination import paginate

from cloudy.core.models import FileModel
from cloudy.logbooks.models import LogBase

from ..auth import require_user
from ..form_data import save_log_from_api
from ..logbooks_access import get_owned_logbook
from ..serialization import log_to_api_dict
from ._common import bearer_auth

router = Router(tags=["logs"])


@router.get("/logbooks/{logbook_id}/logs", response=list[dict], auth=bearer_auth)
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
    return [log_to_api_dict(log._cast().to_json(serialize=False)) for log in qs.order_by("-date")]


@router.get("/logbooks/{logbook_id}/logs/{log_id}", response=dict, auth=bearer_auth)
def get_log(request: HttpRequest, logbook_id: int, log_id: int):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    log = LogBase.get_by_id(log_id)
    if log is None or log.lbook_id != logbook.id or log.deleted:
        raise HttpError(404, "Log not found")
    return log_to_api_dict(log._cast().to_json(serialize=False))


@router.post("/logbooks/{logbook_id}/logs", response={201: dict}, auth=bearer_auth)
def create_log(request: HttpRequest, logbook_id: int, payload: dict = Body(...)):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    try:
        log = save_log_from_api(user, logbook, payload)
    except ValueError as exc:
        raise HttpError(400, str(exc)) from exc
    return 201, log_to_api_dict(log._cast().to_json(serialize=False))


@router.put("/logbooks/{logbook_id}/logs/{log_id}", response=dict, auth=bearer_auth)
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
    return log_to_api_dict(log._cast().to_json(serialize=False))


@router.delete("/logbooks/{logbook_id}/logs/{log_id}", response={204: None}, auth=bearer_auth)
def delete_log(request: HttpRequest, logbook_id: int, log_id: int):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    log = LogBase.get_by_id(log_id)
    if log is None or log.lbook_id != logbook.id:
        raise HttpError(404, "Log not found")
    log.deleted = True
    log.save()
    return 204, None


@router.post("/logbooks/{logbook_id}/logs/{log_id}/files", response=dict, auth=bearer_auth)
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
    return {"url": fobject.file.url}


@router.delete("/logbooks/{logbook_id}/logs/{log_id}/files/{file_id}", response={204: None}, auth=bearer_auth)
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
