import pytest
from django.contrib.auth.models import User
from django.forms.renderers import DjangoTemplates
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from cloudy.accounts.models import UserProfile
from cloudy.core.fields import DictionaryWidget
from cloudy.core.widgets import HorizontalRadioSelect
from cloudy.DGAC_avion_logbook.models import DGACAvionLogBook


def test_horizontal_radio_renders_each_label_once():
    widget = HorizontalRadioSelect(choices=((0, "SE"), (1, "ME"), (-1, "Aucun")))
    html = widget.render("single_pilot_se_me", "0", attrs={"id": "id_single_pilot_se_me"})

    assert html.count("SE") == 1
    assert html.count("ME") == 1
    assert html.count("Aucun") == 1
    assert html.count("<label") == 3
    assert html.count("label-radio") == 3
    assert html.count("radio-inline") == 3
    assert 'id="id_single_pilot_se_me_0"' in html
    assert "checked" in html


def test_dictionary_widget_accepts_renderer():
    html = DictionaryWidget().render(
        "reports",
        {"mono_ncdb": 90},
        attrs={"id": "id_reports"},
        renderer=DjangoTemplates(),
    )

    assert "<textarea" in html
    assert 'name="reports"' in html
    assert "{&quot;mono_ncdb&quot;: 90}" in html


@pytest.mark.django_db
def test_admin_dgac_logbook_change_renders_reports():
    User.objects.create_superuser("staff", "staff@example.com", "secret")
    owner = User.objects.create_user("pilot", "pilot@example.com", "secret")
    UserProfile.objects.create(user=owner, dob="1990-01-01")
    logbook = DGACAvionLogBook(ownr=owner, name="Carnet", cat="helicopter_dgac", update=timezone.now())
    logbook.reports = {"mono_ncdb": 90}
    logbook.save()

    client = Client()
    client.login(username="staff", password="secret")
    response = client.get(reverse("admin:DGAC_avion_logbook_dgacavionlogbook_change", args=[logbook.pk]))

    assert response.status_code == 200
    assert b"mono_ncdb" in response.content


@pytest.mark.django_db
def test_admin_view_on_site_redirects_to_logbook():
    User.objects.create_superuser("staff", "staff@example.com", "secret")
    owner = User.objects.create_user("pilot", "pilot@example.com", "secret")
    UserProfile.objects.create(user=owner, dob="1990-01-01")
    logbook = DGACAvionLogBook(ownr=owner, name="Carnet", cat="helicopter_dgac", update=timezone.now())
    logbook.save()

    assert logbook.get_absolute_url() == f"/logbooks/{logbook.pk}/"

    client = Client()
    client.login(username="staff", password="secret")
    content_type_id = logbook.content_type_id
    response = client.get(f"/admin/r/{content_type_id}/{logbook.pk}/")

    assert response.status_code == 302
    assert response.url.endswith(f"/logbooks/{logbook.pk}/")
