from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from cloudy.aircrafts.models import Aircraft
from cloudy.logbooks.models import LogBookBase


class AircraftTest(TestCase):
    fixtures = ["testing_data.json"]

    def _create_logbook(self):
        """Helper to create a fresh new logbook."""
        data = {"plane_dgac": 1}
        resp = self.c.post(reverse("logbooks:addlogbook"), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "DGAC Avion", 1)
        return LogBookBase.objects.all()[0]

    def setUp(self):
        self.c = Client()

    def test_create_same_id(self):
        """
        Make sure a user can create multiple airplane with the same registration
        plate on different logbooks, but not on the same.

        Used as a refactoring tool.
        """
        self.c.login(email="pilot@example.com", password="azeaze")

        logbook1 = self._create_logbook()
        data = {"logbook": logbook1.id, "imma": "IMMA", "type": "FOO", "airport": "BAR"}
        resp = self.c.post(reverse("logbooks:aircrafts_form", args=[logbook1.pk]), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(logbook1.aircraft_set.count(), 1)

        resp = self.c.post(reverse("logbooks:aircrafts_form", args=[logbook1.pk]), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(
            resp.context["form_craft"],
            None,
            "Vous ne pouvez pas posséder deux aéronefs avec la même immatriculation sure le même carnet.",
        )
        self.assertEqual(logbook1.aircraft_set.count(), 1)

        logbook2 = self._create_logbook()
        data = {"logbook": logbook2.id, "imma": "IMMA", "type": "FOO", "airport": "BAR"}
        resp = self.c.post(reverse("logbooks:aircrafts_form", args=[logbook2.pk]), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(logbook2.aircraft_set.count(), 1)

    def test_wrong_plan(self):
        self.c.login(email="simple@example.com", password="azeaze")

        logbook1 = self._create_logbook()
        data = {"logbook": logbook1.id, "imma": "IMMA", "type": "FOO", "airport": "BAR"}
        resp = self.c.post(reverse("logbooks:aircrafts_form", args=[logbook1.pk]), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(logbook1.aircraft_set.count(), 1)

        data = {"logbook": logbook1.id, "imma": "IMMABIS", "type": "FOO", "airport": "BAR"}
        resp = self.c.post(reverse("logbooks:aircrafts_form", args=[logbook1.pk]), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(
            resp.context["form_craft"],
            None,
            "Vous devez souscrire à l'offre First Class afin de pouvoir enregistrer plus d'un aéronef.",
        )
        self.assertEqual(logbook1.aircraft_set.count(), 1)

    def test_normalize_imma_uppercase(self):
        self.c.login(email="simple@example.com", password="azeaze")

        logbook1 = self._create_logbook()
        data = {"logbook": logbook1.id, "imma": "imma", "type": "FOO", "airport": "BAR"}
        resp = self.c.post(reverse("logbooks:aircrafts_form", args=[logbook1.pk]), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(logbook1.aircraft_set.count(), 1)
        self.assertEqual(Aircraft.objects.get(logbook=logbook1).imma, "IMMA")
