import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from cloudy.accounts.forms import birth_date_year_range, CloudyRegistrationForm
from cloudy.accounts.models import UserProfile


@pytest.fixture
def user_with_profile(db):
    user = User.objects.create_user("smoke", "smoke@example.com", "secret")
    UserProfile.objects.create(user=user, dob="1990-01-01")
    return user


@pytest.mark.django_db
def test_login_page_renders():
    response = Client().get(reverse("auth_login"))
    assert response.status_code == 200
    assert reverse("password_reset").encode() in response.content


@pytest.mark.django_db
def test_password_reset_page_renders():
    response = Client().get("/accounts/password/reset/")
    assert response.status_code == 200
    assert reverse("password_reset") == "/accounts/password/reset/"


@pytest.mark.django_db
def test_home_page_renders():
    response = Client().get(reverse("home"))
    assert response.status_code == 200
    assert b"/mobile/" not in response.content
    assert "Cloudy sur votre mobile".encode() not in response.content


@pytest.mark.django_db
def test_gcu_lists_sas_cloudy_saint_jacques():
    response = Client().get(reverse("gcu"))
    assert response.status_code == 200
    html = response.content.decode()
    assert "SAS CLOUDY" in html
    assert "22 rue du Temple de Blosne" in html
    assert "35136 Saint-Jacques-de-la-Lande" in html
    assert "https://github.com/Natim/cloudy" in html
    assert "GNU AGPL" in html
    assert "D'CLIC" not in html


def test_fcl1080_csv_empty_synthetic_date_is_none():
    from cloudy.FCL1080.models import FCL1080LogBook

    rules = {rule[0]: rule for rule in FCL1080LogBook.csv_rules(None)}
    assert rules["synthetic_date"][2] is None
    assert rules["synthetic_time"][2] == 0


def test_registration_birth_date_years_exclude_recent_years():
    from datetime import date

    today = date.today()
    years = list(birth_date_year_range())
    assert years
    assert max(years) == today.year - 14
    assert min(years) == today.year - 100
    assert today.year not in years


@pytest.mark.django_db
def test_registration_rejects_pilot_younger_than_14():
    from datetime import date

    form = CloudyRegistrationForm(
        data={
            "first_name": "Jean",
            "last_name": "Dupont",
            "dob_year": str(date.today().year - 5),
            "dob_month": "1",
            "dob_day": "1",
            "email": "young@example.com",
            "password1": "secret123",
            "password2": "secret123",
            "tos": True,
        }
    )
    assert not form.is_valid()
    assert "dob" in form.errors


@pytest.mark.django_db
def test_registration_redirects_to_complete_page():
    from datetime import date

    from constance import config

    previous = config.SIGNUP_AUTHORIZED
    config.SIGNUP_AUTHORIZED = True
    try:
        today = date.today()
        response = Client().post(
            reverse("register"),
            {
                "first_name": "Jean",
                "last_name": "Dupont",
                "dob_year": str(today.year - 30),
                "dob_month": "6",
                "dob_day": "25",
                "email": "pilot+demo@example.com",
                "password1": "ValidPass123!",
                "password2": "ValidPass123!",
                "tos": True,
                "website": "",
            },
        )
        assert response.status_code == 302
        assert response.url.startswith(reverse("django_registration_complete"))
        assert "email=pilot%2Bdemo%40example.com" in response.url
        complete = Client().get(response.url)
        assert complete.status_code == 200
        assert b"pilot+demo@example.com" in complete.content
        assert b"pilot demo@example.com" not in complete.content
    finally:
        config.SIGNUP_AUTHORIZED = previous


@pytest.mark.django_db
def test_activation_page_renders_and_activates_user():
    from django.contrib.auth.models import User
    from django.core import signing
    from django_registration.backends.activation import REGISTRATION_SALT

    user = User.objects.create_user("DUPONT-abcde", "pilot+demo@example.com", "secret")
    user.is_active = False
    user.save()
    key = signing.dumps(obj=user.get_username(), salt=REGISTRATION_SALT)

    client = Client()
    get_response = client.get(reverse("django_registration_activate"), {"activation_key": key})
    assert get_response.status_code == 200
    assert b"activation-form" in get_response.content

    post_response = client.post(reverse("django_registration_activate"), {"activation_key": key})
    assert post_response.status_code == 302
    assert post_response.url == reverse("django_registration_activation_complete")
    user.refresh_from_db()
    assert user.is_active

    complete = client.get(post_response.url)
    assert complete.status_code == 200
    assert "Activation du compte réussie".encode() in complete.content


@pytest.mark.django_db
def test_register_disallowed_when_signup_closed():
    from constance import config

    previous = config.SIGNUP_AUTHORIZED
    config.SIGNUP_AUTHORIZED = False
    try:
        response = Client().get(reverse("register"))
        assert response.status_code == 302
        assert response.url == reverse("django_registration_disallowed")
    finally:
        config.SIGNUP_AUTHORIZED = previous


def test_nth_filter_indexes_list():
    from cloudy.logbooks.templatetags.logbook_tags import nth

    logs = ["a", "b", "c"]
    assert nth(logs, 1) == "b"
    assert nth(logs, 99) is None


@pytest.mark.django_db
def test_login_with_email_when_username_differs():
    User.objects.create_user("SLUG-abc12", "pilot@example.com", "secret")
    client = Client()
    response = client.post(
        reverse("auth_login"),
        {"email": "Pilot@example.com", "password": "secret"},
    )
    assert response.status_code == 302
    assert client.session.get("_auth_user_id")


@pytest.mark.django_db
def test_logout_requires_post(user_with_profile):
    client = Client()
    client.force_login(user_with_profile)
    assert client.get(reverse("auth_logout")).status_code == 405

    response = client.post(reverse("auth_logout"))
    assert response.status_code == 302
    assert response.url == "/"
    assert not client.session.get("_auth_user_id")


def test_alerts_url_reverses():
    assert reverse("alerts:qualification") == "/alerts/qualifications/"
    assert reverse("alerts:qualification_detail", args=[671]) == "/alerts/qualifications/671/"
    assert reverse("alerts:medical") == "/alerts/medicals/"
    assert reverse("alerts:medical_detail", args=[12]) == "/alerts/medicals/12/"
    assert reverse("alerts:glide") == "/alerts/glide/"
    assert reverse("alerts:glide_detail", args=[3]) == "/alerts/glide/3/"
    assert reverse("alerts:delete_qualification", args=[671]) == "/alerts/qualifications/delete/671/"
    assert reverse("alerts:delete_medical", args=[12]) == "/alerts/medicals/delete/12/"
    assert reverse("alerts:delete_glide", args=[3]) == "/alerts/glide/delete/3/"


def test_alerts_qualifications_list_renders(user_with_profile):
    from datetime import date

    from cloudy.alerts.models import Qualification, QualificationType

    user_with_profile.userprofile.plan = 2
    user_with_profile.userprofile.save()

    license_type = QualificationType.objects.create(
        categ="qualification",
        type="w_expiry",
        sub_type="plane",
        name="PPL(A)",
        duration="24",
    )
    Qualification.objects.create(
        ownr=user_with_profile,
        license_type=license_type,
        achievement_date=date(2020, 1, 1),
        expiry_date=date(2026, 1, 1),
    )

    client = Client()
    assert client.login(username="smoke", password="secret")

    response = client.get(reverse("alerts:qualification"))

    assert response.status_code == 200
    assert b"PPL(A)" in response.content
    assert b"/alerts/qualifications/" in response.content


def test_graphs_ajax_urls_resolve():
    from django.urls import resolve

    assert reverse("stats:graphs_data") == "/graphs/data/"
    assert reverse("stats:count_foo") == "/graphs/count_foo/"
    assert reverse("stats:airports") == "/graphs/count_airports/"
    assert reverse("stats:get_choices") == "/graphs/get_choices/"
    assert reverse("stats:map_places") == "/graphs/map/"
    assert resolve("/graphs/data/").url_name == "graphs_data"
    assert resolve("/graphs/count_foo/").url_name == "count_foo"
    assert resolve("/graphs/count_airports/").url_name == "airports"
    assert resolve("/graphs/get_choices/").url_name == "get_choices"
    assert resolve("/graphs/map/").url_name == "map_places"


@pytest.mark.django_db
def test_airport_for_place_accepts_icao_and_name():
    from cloudy.stats.models import Airport
    from cloudy.stats.views import airport_for_place

    Airport.objects.create(
        iata="CDG",
        icao="LFPG",
        location="Paris",
        airport="Paris-Charles-de-Gaulle",
        country="France",
        coordinates_lat="49.0097",
        coordinates_lng="2.5479",
    )
    assert airport_for_place("LFPG").icao == "LFPG"
    # Two-token strings used to IndexError in production (name = tab[2]).
    assert airport_for_place("LFPG PARIS").icao == "LFPG"
    labeled = airport_for_place("LFPG - Paris-Charles-de-Gaulle")
    assert labeled is not None
    assert labeled.icao == "LFPG"
    assert labeled.airport == "Paris-Charles-de-Gaulle"
    assert airport_for_place("") is None
    assert airport_for_place("XXXX") is None


def test_graphs_map_returns_json_array(user_with_profile):
    import json
    from datetime import datetime

    from cloudy.DGAC_avion_logbook.models import DGACAvionLog, DGACAvionLogBook
    from cloudy.stats.models import Airport

    Airport.objects.create(
        iata="CDG",
        icao="LFPG",
        location="Paris",
        airport="Paris-Charles-de-Gaulle",
        country="France",
        coordinates_lat="49.0097",
        coordinates_lng="2.5479",
    )
    logbook = DGACAvionLogBook(ownr=user_with_profile, name="map-test", cat="plane_dgac")
    logbook.save()
    now = datetime.now()
    DGACAvionLog.objects.create(
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
        mono_jcdb=60,
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
        nbrto=1,
        nbrla=1,
        airpdep="LFPG PARIS",
        airpar="LFPG",
        staffob="",
        optional_filter="",
    )

    payload = json.dumps({"begin_date": "none", "end_date": "none", "logbook_id": str(logbook.pk)})
    client = Client()
    client.login(username="smoke", password="secret")
    response = client.get(reverse("stats:map_places"), {"payload": payload})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data != []
    assert data[0][0] == "49.0097"


def test_logbooks_home_renders_for_logged_in_user(user_with_profile):
    """Renders the logbook list, which reads LogBookBase and site_base_logbook.html.

    This exercises the udate/update column mapping and the logbook base template; a
    mismatch in either produces a 500 rather than a failed assertion elsewhere.
    """
    client = Client()
    assert client.login(username="smoke", password="secret")

    response = client.get(reverse("logbooks:home"))

    assert response.status_code == 200


def test_json_helpers_use_content_type():
    from cloudy.utils import json_fail, json_ok

    ok = json_ok({"ok": True})
    fail = json_fail("nope")
    assert ok.status_code == 200
    assert "application/json" in ok["Content-Type"]
    assert fail.status_code == 200
    assert "application/json" in fail["Content-Type"]


def test_logbook_pdf_export_uses_content_type(user_with_profile, monkeypatch):
    from cloudy.DGAC_avion_logbook.models import DGACAvionLogBook

    user_with_profile.userprofile.plan = 2
    user_with_profile.userprofile.save()
    logbook = DGACAvionLogBook(ownr=user_with_profile, name="export-test", cat="plane_dgac")
    logbook.save()

    def fake_pdf(self, http_response, title, show_cuts=False):
        http_response.write(b"%PDF-fake")

    monkeypatch.setattr(DGACAvionLogBook, "attach_pdf_to_http_response", fake_pdf)

    client = Client()
    assert client.login(username="smoke", password="secret")
    response = client.get(reverse("logbooks:export", args=[logbook.pk, "pdf"]))

    assert response.status_code == 200
    assert "application/pdf" in response["Content-Type"]
    assert response.content.startswith(b"%PDF-fake")


def test_dgac_avion_pdf_header_closes_reports_paragraph():
    from cloudy.DGAC_avion_logbook.dgac_avion_pdfgen import gen_header_left

    header = gen_header_left()
    assert header is not None


def test_fcl1080_pdf_builds_empty_logbook():
    from io import BytesIO

    from cloudy.FCL1080.fcl1080_pdfgen import gen_carnet_de_vol, min_to_str

    assert min_to_str(0) == ""
    assert min_to_str(60) == "01:00"
    assert min_to_str(90) == "01:30"

    from cloudy.FCL1080.fcl1080_pdfgen import _footer_hmin_cell_helper

    hours_mins = []
    _footer_hmin_cell_helper(hours_mins, 956)
    assert hours_mins == [15, 56]
    hours_mins = []
    _footer_hmin_cell_helper(hours_mins, 956.0)
    assert hours_mins == [15, 56]
    assert isinstance(hours_mins[0], int)

    buf = BytesIO()
    gen_carnet_de_vol(http_response=buf, title="test", show_cuts=False, logs=[], reports={})
    assert buf.getvalue().startswith(b"%PDF")


def test_fcl1080_pdf_builds_with_one_log():
    from datetime import datetime
    from io import BytesIO
    from types import SimpleNamespace

    from cloudy.FCL1080.fcl1080_pdfgen import gen_carnet_de_vol

    log = SimpleNamespace(
        date=datetime(2025, 1, 15),
        departure_place="LFRN",
        departure_time=480,
        arrival_place="LFPG",
        arrival_time=540,
        aircraft_type="C172",
        aircraft_imma="F-TEST",
        single_pilot_se=True,
        single_pilot_me=False,
        single_pilot_time=60,
        multi_pilot_time=0,
        total_time_flight=60,
        name_pic="SELF",
        take_off_day=1,
        take_off_night=0,
        landing_day=1,
        landing_night=0,
        synthetic_time=0,
        synthetic_date=None,
        synthetic_type="",
        obs="",
        pilot_time_dual=0,
        pilot_timpe_cop=0,
        op_time_ifr=0,
        op_time_night=0,
        pilot_time_in_cmd=60,
        pilot_time_inst=0,
    )
    buf = BytesIO()
    gen_carnet_de_vol(http_response=buf, title="test", show_cuts=False, logs=[log], reports={})
    assert buf.getvalue().startswith(b"%PDF")


def test_server_error_renders_cloudy_page_without_request_context():
    """Django's 500 handler renders 500.html with an empty context."""
    from django.template.loader import get_template
    from django.test import RequestFactory
    from django.views.defaults import server_error

    html = get_template("500.html").render({})
    assert "error500" in html
    assert "Retour à l'accueil" in html
    assert "Server Error (500)" not in html

    response = server_error(RequestFactory().get("/logbooks/4385/export/pdf/"))
    assert response.status_code == 500
    body = response.content.decode()
    assert 'class="error500"' in body
    assert "features.css" in body
    assert "Server Error (500)" not in body
