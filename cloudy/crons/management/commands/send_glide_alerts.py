"""Port of legacy glides_alerts cron - sliding qualification alerts."""

from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

import cloudy.alerts.dispatch as dispatch
from cloudy.alerts.models import AlertGlissante, QualificationGlissante


class Command(BaseCommand):
    help = "Send gliding qualification sliding-window alert emails."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        end = datetime.now().date()

        for qualification in QualificationGlissante.objects.select_related("loogbook"):
            logbook = qualification.loogbook
            try:
                alert = AlertGlissante.objects.get(qualif=qualification)
            except AlertGlissante.DoesNotExist:
                continue

            if qualification.duree_unity == "annee":
                begin = datetime(end.year - qualification.duree_int, end.month, end.day).date()
            elif qualification.duree_unity == "mois":
                begin = end - timedelta(days=qualification.duree_int * 30)
            else:
                begin = end - timedelta(days=qualification.duree_int)

            totals = logbook.get_totals(logbook.totals_page_totals(), time_slice=(begin, end), reports=False)
            val_log = totals.get("total_flight_hours", 0)

            if not alert.sent and val_log < qualification.experience_int:
                method = getattr(dispatch, alert.kind)
                method(
                    qualification,
                    recursive=False,
                    delta=alert.days_before,
                    draft=dry_run,
                )
                if not dry_run:
                    alert.sent = True
                    alert.save()
            elif alert.sent and val_log >= qualification.experience_int:
                if not dry_run:
                    alert.sent = False
                    alert.last_value = 0
                    alert.save()

        self.stdout.write(self.style.SUCCESS("Glide alerts done"))
