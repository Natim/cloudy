from django.contrib import admin

from .models import DGACPlaneurLog, DGACPlaneurLogBook


class DGACPlaneurLogBookAdmin(admin.ModelAdmin):
    list_display = ("ownr", "name", "cat", "visbl", "deleted", "cdate", "update")
    list_filter = ("visbl", "deleted", "cat", "cdate")
    search_fields = ["name"]


class DGACPlaneurLogAdmin(admin.ModelAdmin):
    list_display = ("lbook", "glider_type", "glider_imma", "cdate", "update", "visbl", "deleted")
    list_filter = ("visbl", "deleted", "cdate")
    search_fields = ["glider_imma"]


admin.site.register(DGACPlaneurLog, DGACPlaneurLogAdmin)
admin.site.register(DGACPlaneurLogBook, DGACPlaneurLogBookAdmin)
