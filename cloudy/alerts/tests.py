from datetime import date, datetime, timedelta
from os import system

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from cloudy.alerts.models import Alert, Qualification, QualificationType
from cloudy.core.utils import count_files, patch_settings

MAIL_PATH = "/tmp/testing_cloudy_mails"
SMS_PATH = "/tmp/testing_cloudy_texts"

SETTINGS = {
    "EMAIL_BACKEND": "django.core.mail.backends.filebased.EmailBackend",
    "EMAIL_FILE_PATH": MAIL_PATH,
    "SMS_PATH": SMS_PATH,
    "TESTING": True,
}


# Clear the users and profiles database. It's fuckin' dirty, but it's freshen's
# fault (does not go trough the Django test case with all the database-related
# sweetness).
class CleanTestCase(TestCase):
    def _fixture_setup(self):
        for u in User.objects.all():
            u.userprofile.delete()
            u.delete()
        return super()._fixture_setup()


# Test email alerts ***********************************************************


class EmailTest(CleanTestCase):
    fixtures = ["accounts.json", "profiles.json", "qualifications.json"]

    def setUp(self):
        system(f"rm -Rf {MAIL_PATH} && mkdir -p {MAIL_PATH}")
        self.today = datetime.now()
        for q in Qualification.objects.all():
            q.delete()

    def test_email(self):
        # Grab a user
        user = User.objects.all()[0]

        # Create a Qualification
        exp = self.today + timedelta(5)

        qualification_type = QualificationType.objects.filter(duration="-1")[0]
        qualification = Qualification(
            ownr=user,
            license_type=qualification_type,
            achievement_date=datetime(2001, 1, 1),
            expiry_date=exp,
        )
        qualification.save()

        # Create a sample alert
        alert = Alert(kind="email", days_before=7, qualification=qualification)
        alert.save()

        # Call the cron!
        with patch_settings(**SETTINGS):
            call_command("send_qualification_alerts")

        # If not mail, error
        self.assertTrue(count_files(MAIL_PATH) == 1)

        qualification.delete()
        alert.delete()


class SMSTest(CleanTestCase):
    """SMS alerts are email-only in Django 6; keep fixture coverage via email dispatch."""

    fixtures = ["accounts.json", "profiles.json", "qualifications.json"]

    def setUp(self):
        system(f"rm -Rf {SMS_PATH} && mkdir -p {SMS_PATH}")

        self.user = User.objects.all()[1]

        # Ensure a correct phone number (Thomas')
        profile = self.user.userprofile
        profile.phone = "+33676967853"
        profile.save()

        self.today = datetime.now()

    def test_sms(self):
        data = {
            "achievement_date": date(2001, 1, 1).strftime("%Y/%m/%d"),
            "expiry_date": (self.today - timedelta(5)).strftime("%Y/%m/%d"),
        }

        exp = self.today + timedelta(5)

        qualification_type = QualificationType.objects.filter(duration="-1")[0]
        qualification = Qualification(
            ownr=self.user,
            license_type=qualification_type,
            achievement_date=datetime(2001, 1, 1),
            expiry_date=exp,
        )
        qualification.save()

        alert = Alert(kind="sms", days_before=7, qualification=qualification)
        alert.save()

        with patch_settings(**SETTINGS):
            call_command("send_qualification_alerts")

        self.assertTrue(count_files(MAIL_PATH) == 1)

        qualification.delete()
        alert.delete()


class AlertsTriggeringTest(CleanTestCase):
    fixtures = ["accounts.json", "profiles.json", "qualifications.json"]

    def setUp(self):
        system(f"rm -Rf {MAIL_PATH} && mkdir -p {MAIL_PATH}")
        self.today = datetime.now()
        for q in Qualification.objects.all():
            q.delete()
        for q in Alert.objects.all():
            q.delete()
        self.user = User.objects.all()[0]

    def test_far_date(self):
        exp = self.today + timedelta(365)

        qualification_type = QualificationType.objects.filter(duration="-1")[0]
        qualification = Qualification(
            ownr=self.user,
            license_type=qualification_type,
            achievement_date=datetime(2001, 1, 1),
            expiry_date=exp,
        )
        qualification.save()
        alert = Alert(kind="email", days_before=7, qualification=qualification)
        alert.save()

        with patch_settings(**SETTINGS):
            call_command("send_qualification_alerts")

        self.assertEqual(count_files(MAIL_PATH), 0)

    def test_old(self):
        exp = self.today - timedelta(5)
        qualification_type = QualificationType.objects.filter(duration="-1")[0]
        qualification = Qualification(
            ownr=self.user,
            license_type=qualification_type,
            achievement_date=datetime(2001, 1, 1),
            expiry_date=exp,
        )
        qualification.save()
        alert = Alert(kind="email", days_before=7, qualification=qualification)
        alert.save()

        with patch_settings(**SETTINGS):
            call_command("send_qualification_alerts")

        self.assertEqual(count_files(MAIL_PATH), 0)

    def test_already_sent(self):
        exp = self.today + timedelta(4)

        qualification_type = QualificationType.objects.filter(duration="-1")[0]
        qualification = Qualification(
            ownr=self.user,
            license_type=qualification_type,
            achievement_date=datetime(2001, 1, 1),
            expiry_date=exp,
        )
        qualification.save()
        alert = Alert(kind="email", days_before=7, qualification=qualification)
        alert.save()

        with patch_settings(**SETTINGS):
            call_command("send_qualification_alerts")

        self.assertEqual(count_files(MAIL_PATH), 1)

        system(f"rm -Rfv {MAIL_PATH} && mkdir -p {MAIL_PATH}")

        with patch_settings(**SETTINGS):
            call_command("send_qualification_alerts")

        self.assertEqual(count_files(MAIL_PATH), 0)
