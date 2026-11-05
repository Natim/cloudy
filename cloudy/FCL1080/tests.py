"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from datetime import date
from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase

from cloudy.FCL1080.forms import COMS_INIT, FCL1080LogForm, OBS_INIT
from cloudy.FCL1080.models import FCL1080LogBook


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


def test_takeoff_landing_tab_order_is_day_then_night():
    logbook = SimpleNamespace(time_format=0, height_format=0, time_format_str="HH:MM", id=1)
    form = FCL1080LogForm(logbook)
    request = RequestFactory().get("/?p=1")
    html = render_to_string(
        "popups/add_log_fcl1080.html",
        {"form": form, "logbook": logbook, "logbook_id": 1, "request": request},
        request=request,
    )
    order = [
        html.index('id="id_take_off_day"'),
        html.index('id="id_landing_day"'),
        html.index('id="id_take_off_night"'),
        html.index('id="id_landing_night"'),
    ]
    assert order == sorted(order)


def _hhmm_field(prefix, hours, minutes):
    return {f"{prefix}_0": str(hours), f"{prefix}_1": str(minutes)}


def _valid_fcl_flight_post(total_minutes=60, role_minutes=None, aircraft_minutes=None):
    if role_minutes is None:
        role_minutes = total_minutes
    if aircraft_minutes is None:
        aircraft_minutes = total_minutes
    data = {
        "date": "01/10/2026",
        "departure_place": "LFPG",
        "departure_time_0": "8",
        "departure_time_1": "0",
        "arrival_place": "LFPO",
        "arrival_time_0": "9",
        "arrival_time_1": "0",
        "aircraft_type": "C172",
        "aircraft_imma": "F-GABC",
        "single_pilot_se_me": "0",
        "name_pic": "Ada",
        "take_off_day": "1",
        "take_off_night": "0",
        "landing_day": "1",
        "landing_night": "0",
        "optional_filter": "",
        "obs": OBS_INIT,
        "coms": COMS_INIT,
        "passengerA": "",
        "passengerB": "",
        "passengerC": "",
    }
    data.update(_hhmm_field("single_pilot_time", aircraft_minutes // 60, aircraft_minutes % 60))
    data.update(_hhmm_field("multi_pilot_time", 0, 0))
    data.update(_hhmm_field("total_time_flight", total_minutes // 60, total_minutes % 60))
    role_hours = role_minutes // 60
    role_mins = role_minutes % 60
    data.update(_hhmm_field("pilot_time_in_cmd", role_hours, role_mins))
    data.update(_hhmm_field("pilot_timpe_cop", 0, 0))
    data.update(_hhmm_field("pilot_time_dual", 0, 0))
    data.update(_hhmm_field("pilot_time_inst", 0, 0))
    data.update(_hhmm_field("op_time_night", 0, 0))
    data.update(_hhmm_field("op_time_ifr", 0, 0))
    data.update(_hhmm_field("synthetic_time", 0, 0))
    return data


class FCL1080LogFormTimeValidationTest(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        from cloudy.accounts.models import UserProfile

        user = User.objects.create_user("fcl-pilot", "fcl@example.com", "secret")
        UserProfile.objects.create(user=user, dob=date(1990, 1, 1))
        self.logbook = FCL1080LogBook(ownr=user, name="FCL", cat="plane_fcl1080")
        self.logbook.save()

    def test_matching_splits_are_valid(self):
        form = FCL1080LogForm(self.logbook, data=_valid_fcl_flight_post())
        self.assertTrue(form.is_valid(), form.errors)

    def test_role_split_must_match_total(self):
        form = FCL1080LogForm(self.logbook, data=_valid_fcl_flight_post(role_minutes=63))
        self.assertFalse(form.is_valid())

    def test_aircraft_split_must_match_total(self):
        form = FCL1080LogForm(self.logbook, data=_valid_fcl_flight_post(aircraft_minutes=57))
        self.assertFalse(form.is_valid())

    def test_synthetic_entry_skips_flight_time_rules(self):
        data = {
            "date": "",
            "synthetic_date": "02/10/2026",
            "synthetic_type": "FNPT II",
            "synthetic_time_0": "1",
            "synthetic_time_1": "0",
            "optional_filter": "",
            "obs": OBS_INIT,
            "coms": COMS_INIT,
            "passengerA": "",
            "passengerB": "",
            "passengerC": "",
            "single_pilot_se_me": "-1",
        }
        data.update(_hhmm_field("single_pilot_time", 0, 0))
        data.update(_hhmm_field("multi_pilot_time", 0, 0))
        data.update(_hhmm_field("total_time_flight", 2, 0))
        data.update(_hhmm_field("pilot_time_in_cmd", 0, 0))
        data.update(_hhmm_field("pilot_timpe_cop", 0, 0))
        data.update(_hhmm_field("pilot_time_dual", 0, 0))
        data.update(_hhmm_field("pilot_time_inst", 0, 0))
        data.update(_hhmm_field("op_time_night", 0, 0))
        data.update(_hhmm_field("op_time_ifr", 0, 0))
        data.update(_hhmm_field("departure_time", 0, 0))
        data.update(_hhmm_field("arrival_time", 0, 0))
        form = FCL1080LogForm(self.logbook, data=data)
        self.assertTrue(form.is_valid(), form.errors)


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
