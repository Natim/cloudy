import pathlib
import random
import string

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from cloudy.core.utils import get_object_or_None

# Class map
from cloudy.logbooks.settings import MAP


class Command(BaseCommand):
    help = """Import csv logs into an existing logbook, or create a new one.

Examples:
  manage.py import_logbook /path/file.csv 2 plane_dgac --lbid my_logbook_id
  manage.py import_logbook /path/file.csv 2 plane_dgac   (creates import_xxxx)
"""

    def add_arguments(self, parser):
        parser.add_argument("csv_file", help="Path to the CSV file to import.")
        parser.add_argument("user_id", type=int, help="Owner of the target logbook.")
        parser.add_argument("logbook_class", choices=sorted(MAP), help="Type of logbook to import into.")
        parser.add_argument(
            "--lbid",
            dest="logbook_id",
            default="",
            help="Import into this existing logbook instead of creating one.",
        )

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        user_id = options["user_id"]
        class_name = options["logbook_class"]
        logbook_id = options["logbook_id"]

        user = get_object_or_None(User, id=user_id)
        if not user:
            raise CommandError("User unknown")

        if not pathlib.Path(csv_file).is_file():
            raise CommandError("File path unknown")

        klass = MAP[class_name]

        if logbook_id:
            try:
                logbook = klass.objects.get(id=logbook_id)
            except klass.DoesNotExist as exc:
                raise CommandError("Logbook does not exist") from exc
        else:
            random_str = "".join(random.choice(string.ascii_letters) for _ in range(4))
            logbook = klass(
                name="import_%s" % random_str,
                ownr=user,
                cdate=timezone.now(),
                cat=class_name,
            )
            logbook.save()
            self.stdout.write("Created logbook %s" % logbook.id)

        result = logbook.import_from_csv(csv_file, delimiter=";")
        self.stdout.write("result %s" % (result,))
        logbook.save()

        self.stdout.write(self.style.SUCCESS("Successfully imported the logbook %s" % logbook.id))
