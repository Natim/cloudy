from django.contrib import admin

from .models import FFPLog, FFPLogBook


class FFPBookAdmin(admin.ModelAdmin):
    list_display = ("ownr", "name", "cat", "visbl", "deleted", "cdate", "update")
    list_filter = ("visbl", "deleted", "cat", "cdate")
    search_fields = ["name"]


class FFPLogAdmin(admin.ModelAdmin):
    list_display = ("lbook", "place", "aircraft", "altitude", "canopy", "visbl", "deleted")
    list_filter = ("visbl", "deleted", "cdate")


admin.site.register(FFPLog, FFPLogAdmin)
admin.site.register(FFPLogBook, FFPBookAdmin)
