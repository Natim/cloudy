from django.contrib import admin

from .models import FCL1080Log, FCL1080LogBook


class FCL1080LogBookAdmin(admin.ModelAdmin):
    list_display = ("ownr", "name", "cat", "visbl", "deleted", "cdate", "update")
    list_filter = ("visbl", "deleted", "cat", "cdate")
    search_fields = ["name"]


class FCL1080LogAdmin(admin.ModelAdmin):
    list_display = (
        "lbook",
        "aircraft_type",
        "aircraft_imma",
        "cdate",
        "update",
        "visbl",
        "deleted",
    )
    list_filter = ("visbl", "deleted", "cdate")
    search_fields = ["aircraft_imma"]


admin.site.register(FCL1080Log, FCL1080LogAdmin)
admin.site.register(FCL1080LogBook, FCL1080LogBookAdmin)
