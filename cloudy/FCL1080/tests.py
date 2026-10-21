"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase

from cloudy.FCL1080.forms import FCL1080LogForm


def test_add_log_form_lists_registration_before_type():
    logbook = SimpleNamespace(time_format=0, height_format=0, time_format_str="HH:MM", id=1)
    form = FCL1080LogForm(logbook)
    request = RequestFactory().get("/?p=1")
    html = render_to_string(
        "popups/add_log_fcl1080.html",
        {"form": form, "logbook": logbook, "logbook_id": 1, "request": request},
        request=request,
    )
    assert html.index('id="id_aircraft_imma"') < html.index('id="id_aircraft_type"')


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
