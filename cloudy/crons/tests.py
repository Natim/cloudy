from datetime import timedelta
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from cloudy.accounts.models import UserProfile


class DowngradeExpiredPlansTest(TestCase):
    def _profile(self, username, *, switch, staff=False, superuser=False):
        user = User.objects.create_user(username, f"{username}@example.com", "secret")
        if staff or superuser:
            user.is_staff = staff
            user.is_superuser = superuser
            user.save(update_fields=["is_staff", "is_superuser"])
        return UserProfile.objects.create(
            user=user,
            dob="1990-01-01",
            plan=2,
            fplan_switch_date=switch,
        )

    def test_dry_run_compares_aware_switch_dates(self):
        expired = timezone.now() - timedelta(days=400)
        self._profile("expired", switch=expired)
        self._profile("recent", switch=timezone.now() - timedelta(days=10))
        self._profile("missing", switch=None)
        self._profile("staffer", switch=expired, staff=True)

        out = StringIO()
        call_command("downgrade_expired_plans", "--dry-run", stdout=out)
        output = out.getvalue()

        self.assertIn("expired@example.com", output)
        self.assertNotIn("recent@example.com", output)
        self.assertNotIn("missing@example.com", output)
        self.assertNotIn("staffer@example.com", output)
        self.assertEqual(UserProfile.objects.get(user__username="expired").plan, 2)

    def test_downgrades_expired_first_class(self):
        self._profile("expired2", switch=timezone.now() - timedelta(days=400))
        call_command("downgrade_expired_plans")
        self.assertEqual(UserProfile.objects.get(user__username="expired2").plan, 1)
