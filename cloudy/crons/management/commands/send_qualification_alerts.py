from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

import cloudy.alerts.dispatch as dispatch
from cloudy.alerts.models import Qualification


class Command(BaseCommand):
    help = "Send qualification expiry alert emails."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = datetime.now().date()

        for qualification in Qualification.objects.all():
            if qualification.license_type.duration == "0":
                continue
            expiry = qualification.expiry_date
            if expiry is None:
                continue
            delta = expiry - now
            if delta < timedelta(seconds=0):
                continue

            for alert in qualification.alert_set.all():
                if alert.sent:
                    if delta.days in {
                        alert.days_before // 2,
                        alert.days_before // 3,
                        0,
                    }:
                        method = getattr(dispatch, alert.kind)
                        method(
                            qualification,
                            alert=alert,
                            delta=delta,
                            name=qualification.license_type.name,
                            draft=dry_run,
                        )
                    continue

                if (delta - timedelta(days=alert.days_before)) <= timedelta(seconds=0):
                    method = getattr(dispatch, alert.kind)
                    method(
                        qualification,
                        alert=alert,
                        delta=delta,
                        name=qualification.license_type.name,
                        draft=dry_run,
                    )
                    if not dry_run:
                        alert.sent = True
                        alert.save()

            qualification.save()

        self.stdout.write(self.style.SUCCESS("Qualification alerts done"))
