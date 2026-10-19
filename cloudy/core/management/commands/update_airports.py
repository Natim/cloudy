import csv
import urllib.request

from django.core.management.base import BaseCommand

from cloudy.stats.models import Airport


class Command(BaseCommand):
    help = "Add new airports codes from Gladstone Family."

    def handle(self, *args, **options):
        with urllib.request.urlopen(
            "http://weather.gladstonefamily.net/cgi-bin/location.pl/pjsg_all_location.csv?csv=1"
        ) as response:
            reader = csv.reader(
                (line.decode("utf-8") for line in response),
                delimiter=",",
                quotechar='"',
            )
            existing_codes = {code.lower() for code in Airport.objects.values_list("icao", flat=True)}
            added = 0

            for row in reader:
                code = row[0]
                if code.lower() not in existing_codes:
                    Airport(
                        iata=code,
                        icao=code,
                        location="",
                        airport=row[2],
                        country=row[4],
                        coordinates_lat=row[5],
                        coordinates_lng=row[6],
                    ).save()
                    added += 1

        self.stdout.write(f"{added} airports codes added.")
