import json

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.test import Client
from django.urls import reverse

from cloudy.accounts.models import UserProfile
from cloudy.aircrafts.models import Aircraft
from cloudy.DGAC_avion_logbook.models import DGACAvionLogBook
from cloudy.logbooks.models import LogBookBase


@pytest.fixture
def owner_with_logbook(db):
    user = User.objects.create_user("owner", "owner@example.com", "secret")
    UserProfile.objects.create(user=user, dob="1990-01-01")
    logbook = DGACAvionLogBook(ownr=user, name="owned", cat="plane_dgac")
    logbook.save()
    return user, logbook


@pytest.fixture
def other_user(db):
    user = User.objects.create_user("other", "other@example.com", "secret")
    UserProfile.objects.create(user=user, dob="1990-01-01")
    return user


@pytest.mark.django_db
def test_existing_for_user_ignores_anonymous_user(db):
    assert LogBookBase.existing_for_user(AnonymousUser()) == []


@pytest.mark.django_db
def test_existing_for_user_accepts_user_pk(owner_with_logbook):
    user, logbook = owner_with_logbook
    books = LogBookBase.existing_for_user(user.pk)
    assert [book.pk for book in books] == [logbook.pk]


@pytest.mark.django_db
def test_add_log_autocomplete_requires_login(owner_with_logbook):
    _, logbook = owner_with_logbook
    response = Client().get(
        reverse("logbooks:add_log_autocomplete", args=[logbook.pk]),
        {"term": "974"},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
def test_airport_autocomplete_requires_login(owner_with_logbook):
    _, logbook = owner_with_logbook
    response = Client().get(
        reverse("logbooks:airport_autocomplete", args=[logbook.pk]),
        {"term": "LFPG"},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
def test_airport_autocomplete_is_not_captured_as_aircraft_id(owner_with_logbook):
    _, logbook = owner_with_logbook
    client = Client()
    client.login(username="owner", password="secret")
    response = client.get(
        reverse("logbooks:airport_autocomplete", args=[logbook.pk]),
        {"term": "cambaie"},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.django_db
def test_add_log_autocomplete_returns_matching_aircraft(owner_with_logbook):
    _, logbook = owner_with_logbook
    Aircraft.objects.create(logbook=logbook, imma="F-974", type="C172", airport="LFPG")
    client = Client()
    client.login(username="owner", password="secret")
    response = client.get(
        reverse("logbooks:add_log_autocomplete", args=[logbook.pk]),
        {"term": "974"},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 200
    assert json.loads(response.content) == [{"value": "F-974", "type": "C172", "airport": "LFPG"}]


@pytest.mark.django_db
def test_add_log_autocomplete_hides_other_users_aircraft(owner_with_logbook, other_user):
    _, logbook = owner_with_logbook
    Aircraft.objects.create(logbook=logbook, imma="F-974", type="C172", airport="LFPG")
    client = Client()
    client.login(username="other", password="secret")
    response = client.get(
        reverse("logbooks:add_log_autocomplete", args=[logbook.pk]),
        {"term": "974"},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 200
    assert json.loads(response.content) == {"success": False, "msg": "Ce carnet n'existe pas"}


@pytest.mark.django_db
def test_stats_map_requires_login(owner_with_logbook):
    _, logbook = owner_with_logbook
    payload = json.dumps({"begin_date": "none", "end_date": "none", "logbook_id": str(logbook.pk)})
    response = Client().get(reverse("stats:map_places"), {"payload": payload})
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
def test_stats_map_denies_other_users_logbook(owner_with_logbook, other_user):
    _, logbook = owner_with_logbook
    client = Client()
    client.login(username="other", password="secret")
    payload = json.dumps({"begin_date": "none", "end_date": "none", "logbook_id": str(logbook.pk)})
    response = client.get(reverse("stats:map_places"), {"payload": payload})
    assert response.status_code == 404


@pytest.mark.django_db
def test_login_rejects_external_redirect(owner_with_logbook):
    user, _ = owner_with_logbook
    client = Client()
    response = client.post(
        reverse("auth_login"),
        {
            "email": user.email,
            "password": "secret",
            "redirect_to": "https://evil.example/phish",
        },
    )
    assert response.status_code == 302
    assert response.url == reverse("logbooks:home")


@pytest.mark.django_db
def test_del_log_rejects_get(owner_with_logbook):
    from datetime import datetime

    from cloudy.DGAC_avion_logbook.models import DGACAvionLog

    user, logbook = owner_with_logbook
    now = datetime.now()
    log = DGACAvionLog.objects.create(
        lbook=logbook,
        date=now,
        cdate=now,
        update=now,
        aeronef_type="C172",
        aeronef_imma="F-TEST",
        fctbrd="CDB",
        natvol="",
        mbr_equipage_jour=0,
        mbr_equipage_nuit=0,
        mono_jdbl=0,
        mono_jcdb=0,
        mono_ndbl=0,
        mono_ncdb=0,
        mul_jdbl=0,
        mul_jcdb=0,
        mul_jcplt=0,
        mul_ndbl=0,
        mul_ncdb=0,
        mul_ncplt=0,
        vai_dbl=0,
        vai_plt=0,
        simu=0,
        ifr=0,
        obs="",
        cmmts="",
        nbrto=0,
        nbrla=0,
        airpdep="",
        airpar="",
        staffob="",
        optional_filter="",
    )
    client = Client()
    client.login(username="owner", password="secret")
    url = reverse("logbooks:del_log", args=[logbook.pk, log.pk])
    response = client.get(url)
    assert response.status_code == 405
    log.refresh_from_db()
    assert log.deleted is False
