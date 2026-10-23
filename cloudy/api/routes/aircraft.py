from django.core.exceptions import ValidationError
from django.http import HttpRequest
from ninja import File, Router, UploadedFile
from ninja.errors import HttpError

from cloudy.aircrafts.models import Aircraft
from cloudy.core.models import FileModel

from ..auth import require_user
from ..logbooks_access import get_owned_logbook
from ..schemas.aircraft import AircraftIn
from ..serialization import aircraft_to_dict
from ._common import bearer_auth

router = Router(tags=["aircraft"])


@router.get("/logbooks/{logbook_id}/aircraft", response=list[dict], auth=bearer_auth)
def list_aircraft(request: HttpRequest, logbook_id: int):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    return [aircraft_to_dict(a) for a in Aircraft.objects.filter(logbook=logbook)]


@router.post("/logbooks/{logbook_id}/aircraft", response={201: dict}, auth=bearer_auth)
def create_aircraft(request: HttpRequest, logbook_id: int, payload: AircraftIn):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    aircraft = Aircraft(
        logbook=logbook,
        imma=payload.registration,
        type=payload.aircraft_type,
        airport=payload.airport,
    )
    try:
        aircraft.full_clean()
        aircraft.save()
    except ValidationError as exc:
        raise HttpError(400, str(exc)) from exc
    return 201, aircraft_to_dict(aircraft)


@router.patch("/logbooks/{logbook_id}/aircraft/{aircraft_id}", response=dict, auth=bearer_auth)
def patch_aircraft(request: HttpRequest, logbook_id: int, aircraft_id: int, payload: AircraftIn):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    try:
        aircraft = Aircraft.objects.get(pk=aircraft_id, logbook=logbook)
    except Aircraft.DoesNotExist as exc:
        raise HttpError(404, "Aircraft not found") from exc
    aircraft.imma = payload.registration
    aircraft.type = payload.aircraft_type
    aircraft.airport = payload.airport
    try:
        aircraft.full_clean()
        aircraft.save()
    except ValidationError as exc:
        raise HttpError(400, str(exc)) from exc
    return aircraft_to_dict(aircraft)


@router.delete("/logbooks/{logbook_id}/aircraft/{aircraft_id}", response={204: None}, auth=bearer_auth)
def delete_aircraft(request: HttpRequest, logbook_id: int, aircraft_id: int):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    deleted, _ = Aircraft.objects.filter(pk=aircraft_id, logbook=logbook).delete()
    if not deleted:
        raise HttpError(404, "Aircraft not found")
    return 204, None


@router.post("/logbooks/{logbook_id}/aircraft/{aircraft_id}/photo", response=dict, auth=bearer_auth)
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
