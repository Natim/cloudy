from operator import itemgetter

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse

from cloudy.alerts.models import Alert, Qualification, QualificationType
from cloudy.core.utils import get_object_or_None, render_to
from cloudy.logbooks.models import LogBase, LogBookBase
from cloudy.stats.models import Airport


@render_to("admin/unknown_airports.html")
@staff_member_required
def unknown_airports(request):
    unknowns = {}
    codes_tuples = LogBase.objects.filter(~Q(airpdep__iexact="", airpar__iexact="")).values_list(
        "airpdep", "airpar"
    )

    airports = [x.lower() for x in Airport.objects.values_list("icao", flat=True)]
    for tup in codes_tuples:
        for value in tup:
            if value.lower() not in airports:
                actual = unknowns.get(value.upper(), 0)
                unknowns[value.upper()] = actual + 1

    sorteds = sorted(unknowns.items(), key=itemgetter(1), reverse=True)

    return {"airports": sorteds}


@render_to("admin/user_logbooks.html")
@staff_member_required
def logbook_admin(request, user_id):
    user = get_object_or_None(User, id=user_id)
    if not user:
        return HttpResponse("No user for this id !")

    return {"user": user}


@render_to("admin/user_alerts.html")
@staff_member_required
def alerts_admin(request, alert_id):
    alert = get_object_or_None(Alert, id=alert_id)
    qualification = get_object_or_None(Qualification, id=alert.qualification_id)
    user = get_object_or_None(User, id=qualification.ownr_id)

    if not user:
        return HttpResponse("No user for this id !")

    qualification_type = get_object_or_None(QualificationType, id=qualification.license_type_id)

    data = {"user": user, "qual": qualification, "qual_type": qualification_type, "alert": alert}
    return data


@staff_member_required
def logbook_delete(request, logbook_id=None):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    lbook_name = ""
    lbook_ownr = None

    try:
        logbook = LogBookBase.get_by_id(logbook_id)

        lbook_name = logbook.name
        lbook_ownr = logbook.ownr
    except LogBookBase.DoesNotExist:
        return Http404("no such logbook")

    logbook.delete()
    messages.success(request, "Le carnet %s vient d'être deleted" % (lbook_name))
    return HttpResponseRedirect(reverse("admin_user_logbooks", kwargs={"user_id": lbook_ownr}))
