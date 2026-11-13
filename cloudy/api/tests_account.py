import json

import jwt
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase

from cloudy.api.auth import issue_access_token, JWT_ALGORITHM, revoke_access_tokens


def bearer(user: User) -> dict[str, str]:
    token, _expires = issue_access_token(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


class ApiTestCase(TestCase):
    fixtures = ["testing_data.json"]

    def setUp(self):
        self.client = Client()

    def post(self, path, body=None, **headers):
        return self.client.post(
            f"/api/v1{path}", data=json.dumps(body or {}), content_type="application/json", **headers
        )


class TokenTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.pilot = User.objects.get(email="pilot@example.com")
        self.headers = bearer(self.pilot)

    def test_refresh_returns_a_new_token(self):
        resp = self.post("/auth/refresh", **self.headers)
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.json()["user_id"], self.pilot.pk)
        fresh = {"HTTP_AUTHORIZATION": f"Bearer {resp.json()['access_token']}"}
        self.assertEqual(self.client.get("/api/v1/logbooks", **fresh).status_code, 200)

    def test_refresh_needs_a_valid_token(self):
        self.assertEqual(self.post("/auth/refresh").status_code, 401)

    def test_revoked_tokens_are_refused(self):
        revoke_access_tokens(self.pilot)
        self.assertEqual(self.client.get("/api/v1/logbooks", **self.headers).status_code, 401)
        self.assertEqual(self.client.get("/api/v1/logbooks", **bearer(self.pilot)).status_code, 200)

    def test_tokens_issued_before_versioning_still_work(self):
        token, _ = issue_access_token(self.pilot)
        claims = jwt.decode(token, options={"verify_signature": False})
        claims.pop("ver")
        legacy = jwt.encode(claims, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)
        resp = self.client.get("/api/v1/logbooks", HTTP_AUTHORIZATION=f"Bearer {legacy}")
        self.assertEqual(resp.status_code, 200)

    def test_password_hash_upgrade_keeps_tokens(self):
        # The fixture hash uses old PBKDF2 settings: signing in rehashes it.
        login = self.post("/auth/token", {"email": "pilot@example.com", "password": "azeaze"})
        self.assertEqual(login.status_code, 200)
        self.pilot.refresh_from_db()
        self.assertNotIn("$1$", self.pilot.password)
        self.assertEqual(self.client.get("/api/v1/logbooks", **self.headers).status_code, 200)
