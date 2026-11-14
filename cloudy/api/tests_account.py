import io
import json
import re
from datetime import date, timedelta

import jwt
from constance.test import override_config
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.utils import timezone
from django.utils.html import escape
from PIL import Image

from cloudy.accounts.models import EmailCode, ProfileSettings, UserProfile
from cloudy.api.auth import issue_access_token, JWT_ALGORITHM, revoke_access_tokens
from cloudy.api.email_codes import _hash as hash_code

STRONG_PASSWORD = "Altimetre-Calage-1013"


def bearer(user: User) -> dict[str, str]:
    token, _expires = issue_access_token(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(buffer, format="PNG")
    return buffer.getvalue()


class ApiTestCase(TestCase):
    fixtures = ["testing_data.json"]

    def setUp(self):
        self.client = Client()

    def post(self, path, body=None, **headers):
        return self.client.post(
            f"/api/v1{path}", data=json.dumps(body or {}), content_type="application/json", **headers
        )

    def patch(self, path, body, **headers):
        return self.client.patch(
            f"/api/v1{path}", data=json.dumps(body), content_type="application/json", **headers
        )

    def delete(self, path, body=None, **headers):
        return self.client.delete(
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


class ProfileTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.pilot = User.objects.get(email="pilot@example.com")
        self.headers = bearer(self.pilot)

    def test_get_me(self):
        resp = self.client.get("/api/v1/me", **self.headers)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["email"], "pilot@example.com")
        self.assertEqual(body["first_name"], "Ada")
        self.assertEqual(body["plan"], "first")
        self.assertIsNone(body["avatar_url"])
        self.assertEqual(self.client.get("/api/v1/me").status_code, 401)

    def test_account_without_pilot_profile_gets_the_account_fields(self):
        staff = User.objects.create_user("staff-no-profile", "staff@example.com", "x")
        resp = self.client.get("/api/v1/me", **bearer(staff))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["email"], "staff@example.com")
        self.assertIsNone(resp.json()["plan"])

    @override_config(DISKSPACE_FREE_MAXMB=25)
    def test_economy_storage_reports_the_configured_quota(self):
        UserProfile.objects.filter(user=self.pilot).update(plan=1, disk_space_balance=3 * 1024 * 1024)
        body = self.client.get("/api/v1/me", **self.headers).json()
        self.assertEqual(body["plan"], "economy")
        self.assertEqual(body["storage"], {"used_bytes": 3 * 1024 * 1024, "limit_bytes": 25 * 1024 * 1024})

    def test_first_class_storage_is_unlimited(self):
        body = self.client.get("/api/v1/me", **self.headers).json()
        self.assertEqual(body["plan"], "first")
        self.assertEqual(body["storage"], {"used_bytes": 0, "limit_bytes": None})

    def test_a_drifted_disk_counter_is_reported_as_zero(self):
        UserProfile.objects.filter(user=self.pilot).update(plan=1, disk_space_balance=-5)
        body = self.client.get("/api/v1/me", **self.headers).json()
        self.assertEqual(body["storage"]["used_bytes"], 0)

    def test_patch_me(self):
        resp = self.patch(
            "/me",
            {"first_name": "grace", "phone": "+33 6 12 34 56 78", "base_aerodrome": "lfpt"},
            **self.headers,
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        body = resp.json()
        self.assertEqual(body["first_name"], "Grace")
        self.assertEqual(body["last_name"], "Pilot")
        self.assertEqual(body["phone"], "+33612345678")
        self.assertEqual(body["base_aerodrome"], "LFPT")
        self.assertEqual(body["storage"], {"used_bytes": 0, "limit_bytes": None})

    def test_patch_me_validates(self):
        resp = self.patch("/me", {"first_name": "", "birth_date": "2020-01-01"}, **self.headers)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(set(resp.json()["errors"]), {"first_name", "birth_date"})

    def test_email_change_needs_the_password(self):
        resp = self.patch("/me", {"email": "ada@example.com"}, **self.headers)
        self.assertEqual(resp.status_code, 401)
        taken = self.patch(
            "/me", {"email": "simple@example.com", "current_password": "azeaze"}, **self.headers
        )
        self.assertEqual(taken.status_code, 409)
        self.assertEqual(taken.json()["code"], "EMAIL_TAKEN")
        ok = self.patch("/me", {"email": "Ada@Example.com", "current_password": "azeaze"}, **self.headers)
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()["email"], "ada@example.com")

    def test_avatar_upload_and_delete(self):
        upload = SimpleUploadedFile("me.png", png_bytes(), content_type="image/png")
        resp = self.client.post("/api/v1/me/avatar", data={"file": upload}, **self.headers)
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertTrue(resp.json()["avatar_url"].startswith("/media/avatars/"))
        self.assertIsNotNone(self.client.get("/api/v1/me", **self.headers).json()["avatar_url"])

        gone = self.delete("/me/avatar", **self.headers)
        self.assertEqual(gone.status_code, 204)
        self.assertIsNone(self.client.get("/api/v1/me", **self.headers).json()["avatar_url"])

    def test_avatar_must_be_an_image(self):
        upload = SimpleUploadedFile("me.png", b"not an image", content_type="image/png")
        resp = self.client.post("/api/v1/me/avatar", data={"file": upload}, **self.headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("file", resp.json()["errors"])

    def test_damaged_image_is_refused(self):
        damaged = bytearray(png_bytes())
        damaged[-20] ^= 0xFF
        upload = SimpleUploadedFile("me.png", bytes(damaged), content_type="image/png")
        resp = self.client.post("/api/v1/me/avatar", data={"file": upload}, **self.headers)
        self.assertEqual(resp.status_code, 400)

    def test_change_password(self):
        wrong = self.post(
            "/me/password", {"current_password": "nope", "new_password": STRONG_PASSWORD}, **self.headers
        )
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(wrong.json()["detail"], "Invalid credentials")

        weak = self.post(
            "/me/password", {"current_password": "azeaze", "new_password": "123"}, **self.headers
        )
        self.assertEqual(weak.status_code, 400)
        self.assertIn("new_password", weak.json()["errors"])

        ok = self.post(
            "/me/password", {"current_password": "azeaze", "new_password": STRONG_PASSWORD}, **self.headers
        )
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/me", **self.headers).status_code, 401)
        new_headers = {"HTTP_AUTHORIZATION": f"Bearer {ok.json()['access_token']}"}
        self.assertEqual(self.client.get("/api/v1/me", **new_headers).status_code, 200)

    def test_notification_settings(self):
        resp = self.client.get("/api/v1/me/settings", **self.headers)
        self.assertEqual(resp.json(), {"email_notifications": True})
        resp = self.patch("/me/settings", {"email_notifications": False}, **self.headers)
        self.assertEqual(resp.json(), {"email_notifications": False})
        self.assertFalse(ProfileSettings.objects.get(user=self.pilot).mail_on_notification)
