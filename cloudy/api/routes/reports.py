from django.http import HttpRequest
from ninja import Body, Router
from ninja.errors import HttpError

from ..auth import require_user
from ..logbooks_access import get_owned_logbook
from ._common import bearer_auth

router = Router(tags=["reports"])


@router.get("/logbooks/{logbook_id}/reports", response=dict, auth=bearer_auth)
def get_reports(request: HttpRequest, logbook_id: int):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    return logbook.reports or {}


@router.put("/logbooks/{logbook_id}/reports", response=dict, auth=bearer_auth)
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
