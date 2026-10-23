import json
from datetime import datetime

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from cloudy.api.auth import issue_access_token, set_api_user
from cloudy.api.mcp_server import get_totals
from cloudy.DGAC_avion_logbook.models import DGACAvionLogBook
from cloudy.stats.service import get_named_totals, LogbookAccessError


def bearer_headers(user: User) -> dict[str, str]:
    token, _expires = issue_access_token(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


class ApiAuthTests(TestCase):
    fixtures = ["testing_data.json"]

    def setUp(self):
        self.client = Client()
        self.pilot = User.objects.get(email="pilot@example.com")

    def test_token_and_bearer(self):
        resp = self.client.post(
            "/api/v1/auth/token",
            data=json.dumps({"email": "pilot@example.com", "password": "azeaze"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["user_id"], self.pilot.pk)
        self.assertEqual(body["token_type"], "bearer")
        self.assertIn("access_token", body)
        self.assertGreater(body["expires_in"], 0)

        bad = self.client.get("/api/v1/logbooks", HTTP_AUTHORIZATION="Bearer invalid")
        self.assertEqual(bad.status_code, 401)

        legacy = self.client.get("/api/v1/logbooks", HTTP_AUTHORIZATION="Bearer TEST_API_KEY")
        self.assertEqual(legacy.status_code, 401)

        ok = self.client.get(
            "/api/v1/logbooks",
            HTTP_AUTHORIZATION=f"Bearer {body['access_token']}",
        )
        self.assertEqual(ok.status_code, 200)


class ApiLogbookTests(TestCase):
    fixtures = ["testing_data.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(email="pilot@example.com")
        self.headers = bearer_headers(self.user)

    def _create_book(self, cat="plane_dgac"):
        resp = self.client.post(
            "/api/v1/logbooks",
            data=json.dumps({"cat": cat}),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        return resp.json()

    def test_dgac_avion_log_crud(self):
        book = self._create_book("plane_dgac")
        payload = {
            "date": "2011-07-04T12:00:00",
            "optional_filter": "",
            "aeronef_type": "T1",
            "aeronef_imma": "M1",
            "fctbrd": "EP",
            "natvol": "N1",
            "mbr_equipage_nuit": 1,
            "airpdep": "",
            "airpar": "",
        }
        created = self.client.post(
            f"/api/v1/logbooks/{book['id']}/logs",
            data=json.dumps(payload),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(created.status_code, 201, created.content)
        log_id = created.json()["id"]

        updated = self.client.put(
            f"/api/v1/logbooks/{book['id']}/logs/{log_id}",
            data=json.dumps({**payload, "natvol": "N2"}),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["natvol"], "N2")

        deleted = self.client.delete(
            f"/api/v1/logbooks/{book['id']}/logs/{log_id}",
            **self.headers,
        )
        self.assertEqual(deleted.status_code, 204)

    def test_fcl1080_log_create(self):
        book = self._create_book("plane_fcl1080")
        payload = {
            "date": "2011-08-01T08:00:00",
            "optional_filter": "",
            "departure_place": "LFPG",
            "arrival_place": "LFPO",
            "departure_time": "08:00",
            "arrival_time": "09:00",
            "aircraft_type": "C172",
            "aircraft_imma": "F-GABC",
            "single_pilot_se": 1,
            "single_pilot_me": 0,
            "total_time_flight": 60,
            "name_pic": "Ada Pilot",
        }
        resp = self.client.post(
            f"/api/v1/logbooks/{book['id']}/logs",
            data=json.dumps(payload),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(resp.status_code, 201, resp.content)

    def test_aircraft_eco_limit(self):
        simple = User.objects.get(email="simple@example.com")
        simple_headers = bearer_headers(simple)
        book = self.client.post(
            "/api/v1/logbooks",
            data=json.dumps({"cat": "plane_dgac"}),
            content_type="application/json",
            **simple_headers,
        )
        self.assertEqual(book.status_code, 201)
        book_id = book.json()["id"]
        first = self.client.post(
            f"/api/v1/logbooks/{book_id}/aircraft",
            data=json.dumps({"imma": "F-AAAA"}),
            content_type="application/json",
            **simple_headers,
        )
        self.assertEqual(first.status_code, 201)
        second = self.client.post(
            f"/api/v1/logbooks/{book_id}/aircraft",
            data=json.dumps({"imma": "F-BBBB"}),
            content_type="application/json",
            **simple_headers,
        )
        self.assertEqual(second.status_code, 400)

    def test_reports_put(self):
        book = self._create_book("plane_dgac")
        reports = {"nbrto": 3, "nbrla": 3, "ifr": 0, "simu": 0}
        for key in (
            "mbr_equipage_jour",
            "mbr_equipage_nuit",
            "mono_jdbl",
            "mono_jcdb",
            "mono_ndbl",
            "mono_ncdb",
            "mul_jdbl",
            "mul_jcdb",
            "mul_jcplt",
            "mul_ndbl",
            "mul_ncdb",
            "mul_ncplt",
            "vai_dbl",
            "vai_plt",
        ):
            reports[key] = 0
        resp = self.client.put(
            f"/api/v1/logbooks/{book['id']}/reports",
            data=json.dumps(reports),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_photo_upload(self):
        book = self._create_book("plane_dgac")
        payload = {
            "date": "2011-07-05T12:00:00",
            "optional_filter": "",
            "aeronef_type": "T1",
            "aeronef_imma": "M1",
            "fctbrd": "EP",
            "natvol": "N1",
            "mbr_equipage_nuit": 1,
        }
        log = self.client.post(
            f"/api/v1/logbooks/{book['id']}/logs",
            data=json.dumps(payload),
            content_type="application/json",
            **self.headers,
        )
        log_id = log.json()["id"]
        upload = SimpleUploadedFile("scan.jpg", b"fake-image-bytes", content_type="image/jpeg")
        resp = self.client.post(
            f"/api/v1/logbooks/{book['id']}/logs/{log_id}/files",
            data={"file": upload},
            **self.headers,
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertIn("path", resp.json())


class McpStatsTests(TestCase):
    fixtures = ["testing_data.json"]

    def setUp(self):
        self.pilot = User.objects.get(email="pilot@example.com")
        self.other = User.objects.get(email="simple@example.com")
        book = DGACAvionLogBook(name="MCP Test", ownr=self.pilot, cdate=datetime.now(), cat="plane_dgac")
        book.save()
        self.logbook_id = book.id

    def test_mcp_get_totals_owner_and_other(self):
        set_api_user(self.pilot)
        result = get_totals(self.logbook_id, ["total_takeoff"], begin_date="", end_date="")
        self.assertIn("total_takeoff", result)

        set_api_user(self.other)
        with self.assertRaises(LogbookAccessError):
            get_named_totals(
                self.other,
                self.logbook_id,
                ["total_takeoff"],
                {"begin_date": "", "end_date": ""},
            )

    def test_mcp_http_requires_key(self):
        resp = self.client.post("/mcp", data="{}", content_type="application/json")
        self.assertEqual(resp.status_code, 403)
