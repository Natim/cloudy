from django.core.management.base import BaseCommand

from cloudy.logbooks.models import LogBookBase
from cloudy.logbooks.paginator import clear_cache


class Command(BaseCommand):
    help = "Purge paginator and totals cache for all logbooks."

    def handle(self, *args, **options):
        logbooks = LogBookBase.objects.all()
        total = logbooks.count()
        self.stdout.write(f"Purging cache of {total} logbooks...")

        for count, logbook in enumerate(logbooks, start=1):
            self.stdout.write(f"\r{count}/{total}", ending="")
            self.stdout.flush()
            logbook.invalidate_totals_cache()
            clear_cache(logbook)

        self.stdout.write(self.style.SUCCESS("\nCache purge complete."))
