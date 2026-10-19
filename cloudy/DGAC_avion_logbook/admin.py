from django.contrib import admin

from .models import DGACAvionLog, DGACAvionLogBook


class DGACAvionLogBookAdmin(admin.ModelAdmin):
    list_display = ("ownr", "name", "cat", "visbl", "deleted", "cdate", "update")
    list_filter = ("visbl", "deleted", "cat", "cdate")
    search_fields = ["name"]


class DGACAvionLogAdmin(admin.ModelAdmin):
    list_display = ("lbook", "aeronef_type", "aeronef_imma", "cdate", "update", "visbl", "deleted")
    list_filter = ("visbl", "deleted", "cdate")
    search_fields = ["aeronef_imma"]


admin.site.register(DGACAvionLog, DGACAvionLogAdmin)
admin.site.register(DGACAvionLogBook, DGACAvionLogBookAdmin)
