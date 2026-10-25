import json
from datetime import datetime

import jwt
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from cloudy.api.auth import issue_access_token, JWT_AUDIENCE, JWT_ISSUER, set_api_user, user_from_access_token
from cloudy.api.mcp_server import get_logbook, get_totals, list_aircraft, list_logs
from cloudy.api.serialization import log_to_api_dict
from cloudy.DGAC_avion_logbook.models import DGACAvionLogBook
from cloudy.stats.service import get_named_totals, LogbookAccessError


def bearer_headers(user: User) -> dict[str, str]:
    token, _expires = issue_access_token(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


class ApiCorsTests(TestCase):
    fixtures = ["testing_data.json"]

    def setUp(self):
        self.client = Client()
        self.pilot = User.objects.get(email="pilot@example.com")
        self.headers = bearer_headers(self.pilot)

    def test_cors_preflight_allows_pwa_origin(self):
        resp = self.client.options(
            "/api/v1/logbooks",
            HTTP_ORIGIN="http://localhost:5173",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization",
        )
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp["Access-Control-Allow-Origin"], "http://localhost:5173")
        self.assertIn("Authorization", resp["Access-Control-Allow-Headers"])

    def test_cors_get_includes_allow_origin(self):
        resp = self.client.get(
            "/api/v1/logbooks",
            HTTP_ORIGIN="https://natim.github.io",
            **self.headers,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Access-Control-Allow-Origin"], "https://natim.github.io")


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

        claims = jwt.decode(
            body["access_token"],
            settings.SECRET_KEY,
            algorithms=["HS256"],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
        for key in ("sub", "iss", "aud", "iat", "exp", "jti"):
            self.assertIn(key, claims)
        self.assertEqual(claims["sub"], str(self.pilot.pk))

        bad = self.client.get("/api/v1/logbooks", HTTP_AUTHORIZATION="Bearer invalid")
        self.assertEqual(bad.status_code, 401)

        legacy = self.client.get("/api/v1/logbooks", HTTP_AUTHORIZATION="Bearer TEST_API_KEY")
        self.assertEqual(legacy.status_code, 401)

        ok = self.client.get(
            "/api/v1/logbooks",
            HTTP_AUTHORIZATION=f"Bearer {body['access_token']}",
        )
        self.assertEqual(ok.status_code, 200)

    def test_token_rejects_missing_claims(self):
        token, _ = issue_access_token(self.pilot)
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
        del payload["jti"]
        bad = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.assertIsNone(user_from_access_token(bad))


class ApiLogbookTests(TestCase):
    fixtures = ["testing_data.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(email="pilot@example.com")
        self.headers = bearer_headers(self.user)

    def _create_book(self, cat="plane_dgac"):
        resp = self.client.post(
            "/api/v1/logbooks",
            data=json.dumps({"category": cat}),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        return resp.json()

    def _dgac_payload(self, **overrides):
        payload = {
            "flight_date": "2011-07-04T12:00:00",
            "optional_filter": "",
            "aircraft_type": "T1",
            "aircraft_registration": "M1",
            "function_on_board": "EP",
            "flight_nature": "N1",
            "crew_night_minutes": 1,
            "departure_airport": "",
            "arrival_airport": "",
        }
        payload.update(overrides)
        return payload

    def test_dgac_avion_log_crud(self):
        book = self._create_book("plane_dgac")
        payload = self._dgac_payload()
        created = self.client.post(
            f"/api/v1/logbooks/{book['id']}/logs",
            data=json.dumps(payload),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(created.status_code, 201, created.content)
        self.assertIn("Location", created)
        self.assertEqual(created.json()["passengers"], [])
        log_id = created.json()["id"]

        patched = self.client.patch(
            f"/api/v1/logbooks/{book['id']}/logs/{log_id}",
            data=json.dumps({"flight_nature": "N2", "comments": "keep-me"}),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(patched.status_code, 200)
        self.assertEqual(patched.json()["flight_nature"], "N2")
        self.assertEqual(patched.json()["aircraft_type"], "T1")
        self.assertEqual(patched.json()["comments"], "keep-me")

        replaced = self.client.put(
            f"/api/v1/logbooks/{book['id']}/logs/{log_id}",
            data=json.dumps(self._dgac_payload(flight_nature="N3")),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(replaced.status_code, 200)
        self.assertEqual(replaced.json()["flight_nature"], "N3")
        self.assertEqual(replaced.json()["comments"], "")

        deleted = self.client.delete(
            f"/api/v1/logbooks/{book['id']}/logs/{log_id}",
            **self.headers,
        )
        self.assertEqual(deleted.status_code, 204)

    def test_glider_dgac_log_create(self):
        book = self._create_book("glider_dgac")
        payload = {
            "flight_date": "2011-08-02T10:00:00",
            "optional_filter": "",
            "aircraft_type": "ASK21",
            "aircraft_registration": "F-CABC",
            "function_on_board": "Pilote",
            "flight_nature": "L",
            "lmode": "R",
            "dual_minutes": 45,
            "departure_airport": "LFXX",
            "arrival_airport": "LFXX",
        }
        resp = self.client.post(
            f"/api/v1/logbooks/{book['id']}/logs",
            data=json.dumps(payload),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        body = resp.json()
        self.assertEqual(body["function_on_board"], "Pilote")
        self.assertEqual(body["flight_nature"], "L")

    def test_fcl1080_log_create(self):
        book = self._create_book("plane_fcl1080")
        payload = {
            "flight_date": "2011-08-01T08:00:00",
            "optional_filter": "",
            "departure_place": "LFPG",
            "arrival_place": "LFPO",
            "departure_time": "08:00",
            "arrival_time": "09:00",
            "aircraft_type": "C172",
            "aircraft_registration": "F-GABC",
            "single_pilot_se": True,
            "single_pilot_me": False,
            "single_pilot_time": 47,
            "total_time_flight": 60,
            "pilot_in_command_name": "Ada Pilot",
            "passengers": ["Anasthasia Beaujot"],
        }
        resp = self.client.post(
            f"/api/v1/logbooks/{book['id']}/logs",
            data=json.dumps(payload),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.json()["passengers"], ["Anasthasia Beaujot"])
        self.assertEqual(resp.json()["single_pilot_time"], 47)
        self.assertIs(resp.json()["single_pilot_se"], True)
        self.assertIs(resp.json()["single_pilot_me"], False)
        self.assertEqual(resp.json()["departure_time"], "08:00")
        self.assertEqual(resp.json()["arrival_time"], "09:00")

    def test_fcl1080_empty_synthetic_date(self):
        book = self._create_book("plane_fcl1080")
        payload = {
            "flight_date": "2011-08-01T08:00:00",
            "optional_filter": "",
            "departure_place": "LFPG",
            "arrival_place": "LFPO",
            "departure_time": "08:00",
            "arrival_time": "09:00",
            "aircraft_type": "C172",
            "aircraft_registration": "F-GABC",
            "single_pilot_se": 1,
            "single_pilot_me": 0,
            "total_time_flight": 60,
            "pilot_in_command_name": "Ada Pilot",
            "synthetic_date": "",
        }
        created = self.client.post(
            f"/api/v1/logbooks/{book['id']}/logs",
            data=json.dumps(payload),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(created.status_code, 201, created.content)
        self.assertNotIn("synthetic_date", created.json())
        log_id = created.json()["id"]

        cleared = self.client.put(
            f"/api/v1/logbooks/{book['id']}/logs/{log_id}",
            data=json.dumps({**payload, "synthetic_date": None}),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(cleared.status_code, 200, cleared.content)
        self.assertNotIn("synthetic_date", cleared.json())

        dated = self.client.put(
            f"/api/v1/logbooks/{book['id']}/logs/{log_id}",
            data=json.dumps({**payload, "synthetic_date": "2011-08-02T00:00:00"}),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(dated.status_code, 200, dated.content)
        self.assertIn("2011-08-02", dated.json()["synthetic_date"])

        invalid = self.client.put(
            f"/api/v1/logbooks/{book['id']}/logs/{log_id}",
            data=json.dumps({**payload, "synthetic_date": "not-a-date"}),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.json()["errors"]["synthetic_date"][0]["message"], "Invalid date-time.")

    def test_aircraft_eco_limit(self):
        simple = User.objects.get(email="simple@example.com")
        simple_headers = bearer_headers(simple)
        book = self.client.post(
            "/api/v1/logbooks",
            data=json.dumps({"category": "plane_dgac"}),
            content_type="application/json",
            **simple_headers,
        )
        self.assertEqual(book.status_code, 201)
        book_id = book.json()["id"]
        first = self.client.post(
            f"/api/v1/logbooks/{book_id}/aircraft",
            data=json.dumps({"registration": "F-AAAA"}),
            content_type="application/json",
            **simple_headers,
        )
        self.assertEqual(first.status_code, 201)
        second = self.client.post(
            f"/api/v1/logbooks/{book_id}/aircraft",
            data=json.dumps({"registration": "F-BBBB"}),
            content_type="application/json",
            **simple_headers,
        )
        self.assertEqual(second.status_code, 400)

    def test_reports_put(self):
        book = self._create_book("plane_dgac")
        reports = {
            "takeoff_count": 3,
            "landing_count": 3,
            "ifr": 0,
            "simulator_minutes": 0,
            "crew_day_minutes": 0,
            "crew_night_minutes": 0,
            "single_engine_day_dual_minutes": 0,
            "single_engine_day_captain_minutes": 0,
            "single_engine_night_dual_minutes": 0,
            "single_engine_night_captain_minutes": 0,
            "multi_engine_day_dual_minutes": 0,
            "multi_engine_day_captain_minutes": 0,
            "multi_engine_day_co_pilot_minutes": 0,
            "multi_engine_night_dual_minutes": 0,
            "multi_engine_night_captain_minutes": 0,
            "multi_engine_night_co_pilot_minutes": 0,
            "instrument_day_dual_minutes": 0,
            "instrument_pilot_minutes": 0,
        }
        resp = self.client.put(
            f"/api/v1/logbooks/{book['id']}/reports",
            data=json.dumps(reports),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.json()["takeoff_count"], 3)

    def test_photo_upload(self):
        book = self._create_book("plane_dgac")
        log = self.client.post(
            f"/api/v1/logbooks/{book['id']}/logs",
            data=json.dumps(self._dgac_payload(flight_date="2011-07-05T12:00:00")),
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
        self.assertEqual(resp.status_code, 201, resp.content)
        body = resp.json()
        self.assertIn("url", body)
        self.assertIn("id", body)

    def test_log_list_page_token(self):
        book = self._create_book("plane_dgac")
        for day in (4, 5, 6):
            self.client.post(
                f"/api/v1/logbooks/{book['id']}/logs",
                data=json.dumps(self._dgac_payload(flight_date=f"2011-07-0{day}T12:00:00")),
                content_type="application/json",
                **self.headers,
            )
        first = self.client.get(
            f"/api/v1/logbooks/{book['id']}/logs?limit=2",
            **self.headers,
        )
        self.assertEqual(first.status_code, 200)
        page1 = first.json()
        self.assertEqual(len(page1["items"]), 2)
        self.assertIsNotNone(page1["next_page_token"])
        second = self.client.get(
            f"/api/v1/logbooks/{book['id']}/logs?limit=2&page_token={page1['next_page_token']}",
            **self.headers,
        )
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(second.json()["items"]), 1)

    def test_plan_required_for_second_logbook(self):
        simple = User.objects.get(email="simple@example.com")
        headers = bearer_headers(simple)
        first = self.client.post(
            "/api/v1/logbooks",
            data=json.dumps({"category": "plane_dgac"}),
            content_type="application/json",
            **headers,
        )
        self.assertEqual(first.status_code, 201)
        second = self.client.post(
            "/api/v1/logbooks",
            data=json.dumps({"category": "plane_dgac", "name": "Second"}),
            content_type="application/json",
            **headers,
        )
        self.assertEqual(second.status_code, 403)
        self.assertEqual(second.json()["code"], "plan_required")


class PassengerSerializationTests(TestCase):
    def test_semicolon_string_becomes_name_list(self):
        data = log_to_api_dict({"staffob": "Anasthasia Beaujot;;", "id": 1})
        self.assertEqual(data["passengers"], ["Anasthasia Beaujot"])
        self.assertNotIn("staffob", data)

    def test_empty_and_blank_slots_are_omitted(self):
        self.assertEqual(log_to_api_dict({"staffob": ""})["passengers"], [])
        self.assertEqual(log_to_api_dict({"staffob": ";;"})["passengers"], [])
        self.assertEqual(log_to_api_dict({"staffob": None})["passengers"], [])

    def test_existing_list_drops_empty_entries(self):
        data = log_to_api_dict({"passengers": ["Ada", "", "Bob"]})
        self.assertEqual(data["passengers"], ["Ada", "Bob"])

    def test_null_takeoff_and_landing_counts_are_zero(self):
        data = log_to_api_dict(
            {
                "take_off_day": None,
                "take_off_night": None,
                "landing_day": None,
                "landing_night": None,
            }
        )
        self.assertEqual(data["take_off_day"], 0)
        self.assertEqual(data["take_off_night"], 0)
        self.assertEqual(data["landing_day"], 0)
        self.assertEqual(data["landing_night"], 0)

    def test_minute_counts_become_utc_clock_times(self):
        data = log_to_api_dict({"departure_time": 465, "arrival_time": 512})
        self.assertEqual(data["departure_time"], "07:45")
        self.assertEqual(data["arrival_time"], "08:32")

    def test_clock_time_strings_are_kept(self):
        data = log_to_api_dict({"departure_time": "08:00", "arrival_time": "09:00"})
        self.assertEqual(data["departure_time"], "08:00")
        self.assertEqual(data["arrival_time"], "09:00")

    def test_present_takeoff_and_landing_counts_are_kept(self):
        data = log_to_api_dict(
            {
                "take_off_day": 5,
                "take_off_night": 0,
                "landing_day": 5,
                "landing_night": 1,
            }
        )
        self.assertEqual(data["take_off_day"], 5)
        self.assertEqual(data["take_off_night"], 0)
        self.assertEqual(data["landing_day"], 5)
        self.assertEqual(data["landing_night"], 1)


class OpenApiSchemaTests(TestCase):
    def test_openapi_json_includes_log_schemas(self):
        resp = self.client.get("/api/v1/openapi.json")
        self.assertEqual(resp.status_code, 200, resp.content)
        schema = resp.json()
        components = schema["components"]["schemas"]
        self.assertIn("LogRead_glider_dgac", components)
        self.assertIn("LogWrite_plane_dgac", components)
        self.assertIn("LogListOut", components)


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
        self.assertEqual(resp.status_code, 401)

    def test_mcp_logbook_aircraft_and_logs(self):
        set_api_user(self.pilot)
        book = get_logbook(self.logbook_id)
        self.assertEqual(book["id"], self.logbook_id)
        self.assertEqual(book["category"], "plane_dgac")

        aircraft = list_aircraft(self.logbook_id)
        self.assertIsInstance(aircraft, list)

        logs = list_logs(self.logbook_id, limit=10)
        self.assertIsInstance(logs, list)

        set_api_user(self.other)
        with self.assertRaises(LogbookAccessError):
            get_logbook(self.logbook_id)
