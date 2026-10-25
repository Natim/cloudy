from django.http import HttpRequest
from ninja import Body, Router

from ..auth import require_user
from ..errors import invalid_payload
from ..form_data import form_errors_to_api
from ..logbooks_access import get_owned_logbook
from ..serialization import reports_to_api_dict
from ..validation import validate_report_body
from ._common import bearer_auth

router = Router(tags=["reports"])


@router.get("/logbooks/{logbook_id}/reports", response=dict, auth=bearer_auth)
def get_reports(request: HttpRequest, logbook_id: int):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    return reports_to_api_dict(logbook.reports)


@router.put("/logbooks/{logbook_id}/reports", response=dict, auth=bearer_auth)
def put_reports(request: HttpRequest, logbook_id: int, payload: dict = Body(...)):
    user = require_user(request)
    logbook = get_owned_logbook(user, logbook_id)
    model_payload = validate_report_body(logbook, payload)
    form_class = logbook._report_form_model()
    reportform = form_class(logbook, model_payload)
    if not reportform.is_valid():
        raise invalid_payload("Invalid report", errors=form_errors_to_api(reportform.errors))
    logbook.reports = reportform.cleaned_data
    logbook.save()
    return reports_to_api_dict(logbook.reports)
