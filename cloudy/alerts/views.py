# System imports {{{
import json

from django.contrib import messages

# }}}
# Django imports {{{
from django.core import serializers
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from cloudy.accounts.decorators import user_has_plan
from cloudy.logbooks.decorators import fetch_logbook
from cloudy.logbooks.models import LogBookBase

from .forms import QualificationForm, QualificationGlissanteForm

# }}}
# Cloudy {{{
from .models import (
    AlertGlissante,
    Qualification,
    QUALIFICATION_SUB_TYPES,
    QUALIFICATION_TYPES,
    QualificationGlissante,
    QualificationGlissanteType,
    QualificationType,
)

# }}}


# Ajax-data views {{{
@user_has_plan(plan=2)
def get_subtype(request):
    """
    Return the list of subtypes for qualifications.
    ("Avion", "Planeur" and so on...)
    """
    return HttpResponse(json.dumps(dict(QUALIFICATION_SUB_TYPES)), content_type="application/json")


@user_has_plan(plan=2)
def get_type(request):
    """
    Return the list of types for qualifications.
    ("w_expiry", "class_type" and so on...)
    """
    return HttpResponse(json.dumps(dict(QUALIFICATION_TYPES)), content_type="application/json")


@user_has_plan(plan=2)
def get_qualifications_list(request):
    """
    Return the list of qualifications for a given (type, sub type) couple.
    """
    qtype = request.GET["type"]
    qsub_type = request.GET["sub_type"]

    filters = {
        "categ": "qualification",
        "type": qtype,
        "sub_type": qsub_type,
    }
    objects = QualificationType.objects.filter(**filters)
    data = serializers.serialize("json", objects)

    return HttpResponse(data, content_type="application/json")


@user_has_plan(plan=2)
def get_qualification(request):
    """
    Return the detail of a qualification OR a medical license. It purposely
    works for both.

    I'm aware of the shitty name.
    """
    pk = request.GET["pk"]

    obj = QualificationType.objects.get(pk=pk)
    # data = serializers.serialize('json', obj)
    data = obj.to_json()

    return HttpResponse(data, content_type="application/json")


@user_has_plan(plan=2)
def get_medicals_list(request):
    """
    Returns the list of the medical licenses.
    We have nothing to filter there.
    """
    objs = QualificationType.objects.filter(categ="medical")
    data = serializers.serialize("json", objs)
    return HttpResponse(data, content_type="application/json")


@user_has_plan(plan=2)
def get_glides_list(request):
    """
    Return the list of qualifications for a given (type, sub type) couple.
    """
    qcateg = request.GET["categ"]

    objects = QualificationGlissanteType.objects.filter(category=qcateg)
    data = serializers.serialize("json", objects)

    return HttpResponse(data, content_type="application/json")


# }}}


@user_has_plan(plan=2)
def qualification(request, uid=None, qtype="qualification"):
    """
    GET + no UID => Display all.
    GET + UID => form to edit.
    POST + no UID => Create qualification.
    POST + UID => Edit qualification.
    """

    qualification = None

    filters = {
        "ownr": request.user,
        "license_type__categ": qtype,
    }
    qualifications = Qualification.objects.filter(**filters).order_by("expiry_date")

    data = {"qualifications": qualifications}

    if uid is not None:
        qualification = get_object_or_404(Qualification, pk=uid, ownr=request.user)
        data["qualification"] = qualification

    if request.method == "POST":
        form = QualificationForm(request.POST, request.FILES, owner=request.user)

        if uid is not None:
            form = QualificationForm(request.POST, request.FILES, instance=qualification, owner=request.user)

        if form.is_valid():
            form.save()
            msg = "Nouvelle qualification ajoutée !"
            if qtype == "medical":
                msg = "Nouveau certificate medical ajouté !"
            messages.success(request, msg)
            return HttpResponseRedirect(reverse("alerts:" + qtype))

    else:
        form = QualificationForm(owner=request.user)

        if uid is not None:
            form = QualificationForm(instance=qualification, owner=request.user)

    data["form"] = form
    data["qtype"] = qtype

    return render(request, "alerts/%s.html" % qtype, data)


@user_has_plan(plan=2)
@fetch_logbook
def glide(request, uid=None, qtype="glide"):
    qualification = None
    qualifications = QualificationGlissante.objects.filter(ownr=request.user)
    logbooks = LogBookBase.objects.filter(ownr=request.user, deleted=False)
    avions = QualificationGlissanteType.objects.filter(category="plane")
    planeurs = QualificationGlissanteType.objects.filter(category="glider")
    helicos = QualificationGlissanteType.objects.filter(category="copter")
    ulms = QualificationGlissanteType.objects.filter(category="ulm")
    parachutes = QualificationGlissanteType.objects.filter(category="para")

    data = {
        "qualifications": qualifications,
        "logbooks": logbooks,
        "avions": avions,
        "planeurs": planeurs,
        "helicos": helicos,
        "ulms": ulms,
        "parachutes": parachutes,
    }

    form = QualificationGlissanteForm()

    if uid is not None:
        qualification = get_object_or_404(QualificationGlissante, pk=uid, ownr=request.user)
        form = QualificationGlissanteForm(instance=qualification)

    if request.method == "POST":
        form = QualificationGlissanteForm(request.POST)

        if form.is_valid():
            if uid is not None:
                qualification.delete()

            categ = form.cleaned_data["subtype"]
            name = form.cleaned_data["qtype"]
            qgtype = QualificationGlissanteType.objects.get(category=categ, name=name)

            logbook_name = form.cleaned_data["logbook_name"]
            logbook = LogBookBase.objects.get(ownr=request.user, name=logbook_name)

            exp_int = form.cleaned_data["experience_int"]
            exp_unity = form.cleaned_data["experience_unity"]
            dur_int = form.cleaned_data["duree_int"]
            dur_unity = form.cleaned_data["duree_unity"]

            new_qualif = QualificationGlissante(
                ownr=request.user,
                license_type=qgtype,
                loogbook=logbook,
                experience_int=exp_int,
                experience_unity=exp_unity,
                duree_int=dur_int,
                duree_unity=dur_unity,
            )
            new_qualif.save()

            new_alert = AlertGlissante(qualif=new_qualif)
            new_alert.save()

            messages.success(request, "Nouvelle qualification ajoutée !")
        return redirect("alerts:" + qtype)

    data["form"] = form
    data["qualification"] = qualification
    data["toto"] = "toto"

    return render(request, "alerts/%s.html" % qtype, data)


@user_has_plan(plan=2)
def delete(request, uid, qtype="qualification"):
    if qtype == "glide":
        QualificationGlissante.objects.get(pk=uid, ownr=request.user).delete()
    else:
        Qualification.objects.get(pk=uid, ownr=request.user).delete()
    return redirect("alerts:" + qtype)
