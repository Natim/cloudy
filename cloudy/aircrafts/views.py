# System imports {{{
import json
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect

# }}}
# Django imports {{{
from django.shortcuts import redirect, render
from django.urls import reverse

from cloudy.core.models import FileModel

# }}}
# Third-party apps {{{
# from annoying.decorators import render_to  # TODO
# }}}
# Cloudy {{{
from cloudy.logbooks.decorators import fetch_logbook
from cloudy.stats.models import Airport

from .forms import AircraftForm
from .models import Aircraft

# }}}


@login_required
@fetch_logbook
# @render_to("aircrafts/index.html")  # TODO
def index(request, logbook_id):
    data = {}
    logbook = request.logbook
    data["logbook"] = logbook
    data["logbooks"] = request.logbooks  # Because our templates are such a mess
    data["aircrafts"] = logbook.aircraft_set.all()
    return data


@login_required
@fetch_logbook
def delete(request, logbook_id, aircraft_id):
    aircraft = Aircraft.objects.get(pk=int(aircraft_id))
    imma = aircraft.imma
    aircraft.delete()
    messages.success(request, "L'aéronef %s vient d'être supprimé." % imma)
    return HttpResponseRedirect(reverse("logbooks:aircrafts_index", args=(request.logbook.id,)))


@fetch_logbook
def add_log_autocomplete(request, logbook_id):
    term = request.GET["term"]
    aircrafts = Aircraft.objects.filter(logbook=request.logbook, imma__icontains=term)
    data = []
    for aircraft in aircrafts:
        elem = {"value": aircraft.imma, "type": aircraft.type, "airport": aircraft.airport}
        data.append(elem)

    return HttpResponse(json.dumps(data), content_type="application/json")


@fetch_logbook
def airport_autocomplete(request, logbook_id):
    term = request.GET["term"]
    icao = r"^[a-zA-Z0-9]{4,10}$"
    data = []
    icao_only = getattr(request.logbook, "cat", "") == "plane_fcl1080"

    def airport_choice(airport):
        label = f"{airport.icao} - {airport.airport}"
        return {
            "label": label,
            "value": airport.icao if icao_only else label,
            "icao": airport.icao,
        }

    if re.match(icao, term) is not None:
        airports = Airport.objects.filter(icao__icontains=term)
        for airport in airports:
            data.append(airport_choice(airport))

    if len(data) == 0:
        if len(term) > 3:
            airports = Airport.objects.filter(airport__icontains=term)
            for airport in airports:
                data.append(airport_choice(airport))

    return HttpResponse(json.dumps(data), content_type="application/json")


@login_required
@fetch_logbook
def form(request, logbook_id, aircraft_id=None):
    aircraft = None
    if aircraft_id is not None:
        aircraft_id = int(aircraft_id)
        aircraft = Aircraft.objects.get(pk=aircraft_id)

    if request.method == "POST":
        form = AircraftForm(request.POST)
        if aircraft_id is not None:
            aircraft = Aircraft.objects.get(pk=aircraft_id)
            form = AircraftForm(request.POST, instance=aircraft)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            if len(request.FILES.keys()) > 0:
                db_file = FileModel(owner=request.user, file=request.FILES["pictures"])
                db_file.save()
                obj.pictures.add(db_file)
            obj.save()
            return HttpResponseRedirect(reverse("logbooks:aircrafts_index", args=(request.logbook.id,)))

    else:
        if not (request.user.userprofile.has_payed_plan() or request.logbook.aircraft_set.all().count() < 1):
            return redirect(reverse("payment:pcloudy") + "?pack=aircrafts")

        form = AircraftForm(
            initial={
                "logbook": request.logbook,
            }
        )
        if aircraft_id is not None:
            aircraft = Aircraft.objects.get(pk=aircraft_id)
            form = AircraftForm(instance=aircraft)

    data = {
        "logbook": request.logbook,
        "logbooks": request.logbooks,
        "form_craft": form,
        "aircraft": aircraft,
    }
    return render(request, "aircrafts/form.html", data)
