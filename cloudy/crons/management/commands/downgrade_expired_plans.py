from datetime import timedelta

from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.utils import timezone

from cloudy.accounts.models import UserProfile
from cloudy.notifications import services as notification


class Command(BaseCommand):
    help = "Downgrade expired First Class users (plan=2 past 385 days)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = timezone.now()
        count = 0

        for profile in UserProfile.objects.filter(plan=2):
            user = profile.user
            if user.is_superuser or user.is_staff:
                continue
            switch = profile.fplan_switch_date
            if switch is None:
                continue
            if now - switch > timedelta(days=385):
                count += 1
                if dry_run:
                    self.stdout.write(f"Would downgrade {user.email}")
                    continue
                profile.plan = 1
                notification.send([user], "firstclass_downgrade", {})
                mail_admins(
                    "Premium account ended !",
                    f"User {user.get_full_name()} ({user.email}) premium plan ended.",
                    fail_silently=True,
                )
                profile.save()

        self.stdout.write(self.style.SUCCESS(f"Processed {count} profiles (dry_run={dry_run})"))
