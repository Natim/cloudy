from django.db.models import Prefetch
from django.http import HttpRequest
from ninja import Body, File, Router, UploadedFile
from ninja.errors import HttpError
from ninja.responses import Response

from cloudy.core.models import FileModel
from cloudy.logbooks.models import LogBase

from ..auth import require_user
from ..errors import storage_quota
from ..form_data import save_log_from_api
from ..logbooks_access import get_owned_logbook
from ..pagination import log_list_response, paginate_logs_queryset, parse_optional_iso_datetime
from ..schemas.common import LogListOut
from ..serialization import log_instance_to_api_dict
from ._common import bearer_auth, resource_location

router = Router(tags=["logs"])


def _log_location(request: HttpRequest, logbook_id: int, log_id: int) -> str:
    return resource_location(request, f"/api/v1/logbooks/{logbook_id}/logs/{log_id}")


def _file_location(request: HttpRequest, logbook_id: int, log_id: int, file_id: int) -> str:
    return resource_location(request, f"/api/v1/logbooks/{logbook_id}/logs/{log_id}/files/{file_id}")


@router.get("/logbooks/{logbook_id}/logs", response=LogListOut, auth=bearer_auth)
def list_logs(
    request: HttpRequest,
    logbook_id: int,
    limit: int = 100,
    page_token: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    start = parse_optional_iso_datetime(date_from, "date_from")
    end = parse_optional_iso_datetime(date_to, "date_to")
    qs = logbook.logs_qs(time_slice=(start, end)).prefetch_related(
        Prefetch("files", queryset=FileModel.objects.filter(deleted=False))
    )
    rows, next_token = paginate_logs_queryset(qs, limit=limit, page_token=page_token)
    items = [log_instance_to_api_dict(log) for log in rows]
    return log_list_response(items, next_token)


@router.get("/logbooks/{logbook_id}/logs/{log_id}", response=dict, auth=bearer_auth)
def get_log(request: HttpRequest, logbook_id: int, log_id: int):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    log = LogBase.get_by_id(log_id)
    if log is None or log.lbook_id != logbook.id or log.deleted:
        raise HttpError(404, "Log not found")
    return log_instance_to_api_dict(log._cast())


@router.post("/logbooks/{logbook_id}/logs", response={201: dict}, auth=bearer_auth)
def create_log(request: HttpRequest, logbook_id: int, payload: dict = Body(...)):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    log = save_log_from_api(user, logbook, payload, partial=False)
    data = log_instance_to_api_dict(log._cast())
    return Response(data, status=201, headers={"Location": _log_location(request, logbook_id, log.pk)})


@router.put("/logbooks/{logbook_id}/logs/{log_id}", response=dict, auth=bearer_auth)
def replace_log(request: HttpRequest, logbook_id: int, log_id: int, payload: dict = Body(...)):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    log = LogBase.get_by_id(log_id)
    if log is None or log.lbook_id != logbook.id or log.deleted:
        raise HttpError(404, "Log not found")
    cast = log._cast()
    updated = save_log_from_api(user, logbook, payload, log=cast, partial=False)
    return log_instance_to_api_dict(updated._cast())


@router.patch("/logbooks/{logbook_id}/logs/{log_id}", response=dict, auth=bearer_auth)
def patch_log(request: HttpRequest, logbook_id: int, log_id: int, payload: dict = Body(...)):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    log = LogBase.get_by_id(log_id)
    if log is None or log.lbook_id != logbook.id or log.deleted:
        raise HttpError(404, "Log not found")
    cast = log._cast()
    updated = save_log_from_api(user, logbook, payload, log=cast, partial=True)
    return log_instance_to_api_dict(updated._cast())


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


@router.post("/logbooks/{logbook_id}/logs/{log_id}/files", response={201: dict}, auth=bearer_auth)
def upload_log_file(
    request: HttpRequest,
    logbook_id: int,
    log_id: int,
    file: UploadedFile = File(...),
):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    if not user.userprofile.can_upload_media():
        raise storage_quota()
    log = LogBase.get_by_id(log_id)
    if log is None or log.lbook_id != logbook.id or log.deleted:
        raise HttpError(404, "Log not found")
    fobject = FileModel(owner=user, file=file)
    fobject.save()
    log.files.add(fobject)
    body = {"id": fobject.pk, "url": fobject.file.url}
    return Response(
        body,
        status=201,
        headers={"Location": _file_location(request, logbook_id, log_id, fobject.pk)},
    )


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
