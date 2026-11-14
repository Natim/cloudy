import json
import re
from datetime import date, timedelta

import jwt
from constance.test import override_config
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.test import Client, TestCase
from django.utils import timezone
from django.utils.html import escape

from cloudy.accounts.models import EmailCode
from cloudy.api.auth import issue_access_token, JWT_ALGORITHM, revoke_access_tokens
from cloudy.api.email_codes import _hash as hash_code

STRONG_PASSWORD = "Altimetre-Calage-1013"


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

    def last_code(self) -> str:
        return re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)


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


@override_config(SIGNUP_AUTHORIZED=True)
class RegistrationTests(ApiTestCase):
    def registration_body(self, **overrides):
        body = {
            "email": "new.pilot@example.com",
            "otp": self.last_code(),
            "firstName": "jeanne",
            "lastName": "durand",
            "password": STRONG_PASSWORD,
            "birthDate": "1990-05-17",
            "phoneNumber": "+2250712345678",
            "baseAerodrome": "lfpn",
        }
        body.update(overrides)
        return body

    def test_full_sign_up_flow(self):
        resp = self.post("/auth/register", {"email": "New.Pilot@example.com"})
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.json()["expires_in"], 600)
        self.assertEqual(mail.outbox[-1].to, ["new.pilot@example.com"])

        verify = self.post("/auth/verify-otp", {"email": "new.pilot@example.com", "otp": self.last_code()})
        self.assertEqual(verify.status_code, 200)
        self.assertEqual(verify.json(), {"valid": True})

        done = self.post("/auth/complete-registration", self.registration_body())
        self.assertEqual(done.status_code, 201, done.content)
        token = done.json()["access_token"]

        user = User.objects.get(email="new.pilot@example.com")
        self.assertTrue(user.is_active)
        self.assertEqual((user.first_name, user.last_name), ("Jeanne", "DURAND"))
        self.assertEqual(user.userprofile.dob, date(1990, 5, 17))
        self.assertEqual(user.userprofile.phone, "+2250712345678")
        self.assertEqual(user.userprofile.aerodrom, "LFPN")
        self.assertEqual(user.userprofile.plan, 1)
        self.assertTrue(user.userprofile.api_key)
        self.assertEqual(
            self.client.get("/api/v1/logbooks", HTTP_AUTHORIZATION=f"Bearer {token}").status_code, 200
        )

        # The code is used up.
        again = self.post("/auth/complete-registration", self.registration_body())
        self.assertEqual(again.status_code, 409)
        self.assertEqual(again.json()["code"], "EMAIL_TAKEN")

    def test_register_existing_email_conflicts(self):
        resp = self.post("/auth/register", {"email": "pilot@example.com"})
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["code"], "EMAIL_TAKEN")
        self.assertEqual(len(mail.outbox), 0)

    def test_register_takes_over_an_unactivated_web_sign_up(self):
        stale = User.objects.create(username="OLD-abcde", email="new.pilot@example.com", is_active=False)
        self.post("/auth/register", {"email": "new.pilot@example.com"})
        done = self.post("/auth/complete-registration", self.registration_body())
        self.assertEqual(done.status_code, 201, done.content)
        stale.refresh_from_db()
        self.assertTrue(stale.is_active)
        self.assertTrue(stale.check_password(STRONG_PASSWORD))
        self.assertEqual(User.objects.filter(email="new.pilot@example.com").count(), 1)

    def test_resend_is_rate_limited(self):
        self.assertEqual(self.post("/auth/register", {"email": "new.pilot@example.com"}).status_code, 200)
        second = self.post("/auth/register", {"email": "new.pilot@example.com"})
        self.assertEqual(second.status_code, 429)
        EmailCode.objects.update(created_at=timezone.now() - timedelta(minutes=2))
        self.assertEqual(self.post("/auth/register", {"email": "new.pilot@example.com"}).status_code, 200)
        self.assertEqual(EmailCode.objects.filter(used_at__isnull=True).count(), 1)

    def test_wrong_and_expired_codes(self):
        self.post("/auth/register", {"email": "new.pilot@example.com"})
        good = self.last_code()
        wrong = "000000" if good != "000000" else "111111"
        resp = self.post("/auth/verify-otp", {"email": "new.pilot@example.com", "otp": wrong})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["code"], "OTP_INVALID")

        EmailCode.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        resp = self.post("/auth/verify-otp", {"email": "new.pilot@example.com", "otp": good})
        self.assertEqual(resp.json()["code"], "OTP_EXPIRED")

    def test_code_is_burnt_after_five_wrong_guesses(self):
        self.post("/auth/register", {"email": "new.pilot@example.com"})
        good = self.last_code()
        wrong = "000000" if good != "000000" else "111111"
        codes = [
            self.post("/auth/verify-otp", {"email": "new.pilot@example.com", "otp": wrong}).json()["code"]
            for _ in range(5)
        ]
        self.assertEqual(codes, ["OTP_INVALID"] * 4 + ["OTP_EXPIRED"])
        resp = self.post("/auth/verify-otp", {"email": "new.pilot@example.com", "otp": good})
        self.assertEqual(resp.json()["code"], "OTP_EXPIRED")

    def test_invalid_fields_are_reported(self):
        self.post("/auth/register", {"email": "new.pilot@example.com"})
        resp = self.post(
            "/auth/complete-registration",
            self.registration_body(
                password="123", birthDate=timezone.now().date().isoformat(), phoneNumber="call me"
            ),
        )
        self.assertEqual(resp.status_code, 400)
        errors = resp.json()["errors"]
        self.assertIn("birth_date", errors)
        self.assertIn("phone", errors)
        self.assertFalse(User.objects.filter(email="new.pilot@example.com").exists())

    def test_weak_password_is_refused(self):
        self.post("/auth/register", {"email": "new.pilot@example.com"})
        resp = self.post("/auth/complete-registration", self.registration_body(password="123"))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("password", resp.json()["errors"])
        self.assertFalse(User.objects.filter(email="new.pilot@example.com").exists())

    def test_code_email_has_an_html_version(self):
        self.post("/auth/register", {"email": "new.pilot@example.com"})
        message = mail.outbox[-1]
        html, mimetype = message.alternatives[0]
        self.assertEqual(mimetype, "text/html")
        self.assertIn(self.last_code(), html)
        self.assertIn("Bienvenue sur Cloudy", html)
        self.assertIn(escape(message.subject), html)

    @override_config(SIGNUP_AUTHORIZED=False)
    def test_closed_sign_up(self):
        resp = self.post("/auth/register", {"email": "new.pilot@example.com"})
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()["code"], "signup_closed")


class PasswordResetTests(ApiTestCase):
    def test_reset_flow_revokes_old_tokens(self):
        pilot = User.objects.get(email="pilot@example.com")
        old_headers = bearer(pilot)

        resp = self.post("/auth/forgot-password", {"email": "PILOT@example.com"})
        self.assertEqual(resp.status_code, 200)
        code = self.last_code()
        self.assertEqual(
            self.post("/auth/verify-otp", {"email": "pilot@example.com", "otp": code}).status_code, 200
        )

        done = self.post(
            "/auth/reset-password", {"email": "pilot@example.com", "otp": code, "password": STRONG_PASSWORD}
        )
        self.assertEqual(done.status_code, 200, done.content)
        self.assertIn("access_token", done.json())

        login = self.post("/auth/token", {"email": "pilot@example.com", "password": STRONG_PASSWORD})
        self.assertEqual(login.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/logbooks", **old_headers).status_code, 401)

        reuse = self.post(
            "/auth/reset-password", {"email": "pilot@example.com", "otp": code, "password": STRONG_PASSWORD}
        )
        self.assertEqual(reuse.json()["code"], "OTP_EXPIRED")

    def test_unknown_email_gets_the_same_answer(self):
        known = self.post("/auth/forgot-password", {"email": "pilot@example.com"})
        unknown = self.post("/auth/forgot-password", {"email": "nobody@example.com"})
        self.assertEqual(known.status_code, unknown.status_code)
        self.assertEqual(known.json(), unknown.json())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Nouveau mot de passe", mail.outbox[0].alternatives[0][0])

    def test_sign_up_code_cannot_reset_a_password(self):
        EmailCode.objects.create(
            email="pilot@example.com",
            purpose=EmailCode.SIGNUP,
            code_hash=hash_code("123456"),
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        resp = self.post(
            "/auth/reset-password",
            {"email": "pilot@example.com", "otp": "123456", "password": STRONG_PASSWORD},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["code"], "OTP_EXPIRED")
