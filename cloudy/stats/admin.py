import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils.encoding import smart_str

from .models import *


def export_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=airports.csv"
    writer = csv.writer(response, csv.excel)
    response.write("\ufeff".encode())  # BOM (optional...Excel needs it to open UTF-8 file properly)
    writer.writerow(
        [
            smart_str("IATA"),
            smart_str("ICAO"),
            smart_str("Location"),
            smart_str("Airport"),
            smart_str("Country"),
            smart_str("Coordinates lat"),
            smart_str("Coordinates lng"),
        ]
    )
    for obj in queryset:
        writer.writerow(
            [
                smart_str(obj.iata),
                smart_str(obj.icao),
                smart_str(obj.location),
                smart_str(obj.airport),
                smart_str(obj.country),
                smart_str(obj.coordinates_lat),
                smart_str(obj.coordinates_lng),
            ]
        )
    return response


export_csv.short_description = "Export CSV"


class AirportAdmin(admin.ModelAdmin):
    search_fields = ["iata", "icao", "location", "airport", "country"]
    actions = [export_csv]


admin.site.register(Airport, AirportAdmin)
