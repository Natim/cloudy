from django.contrib import admin

from .models import FFPLUMUlmLog, FFPLUMUlmLogBook


class FFPLUMUlmLogBookAdmin(admin.ModelAdmin):
    list_display = ("ownr", "name", "cat", "visbl", "deleted", "cdate", "update")
    list_filter = ("visbl", "deleted", "cat", "cdate")
    search_fields = ["name"]


class FFPLUMUlmLogAdmin(admin.ModelAdmin):
    list_display = ("lbook", "ulm_type", "ulm_imma", "cdate", "update", "visbl", "deleted")
    list_filter = ("visbl", "deleted", "cdate")
    search_fields = ["ulm_imma"]


admin.site.register(FFPLUMUlmLog, FFPLUMUlmLogAdmin)
admin.site.register(FFPLUMUlmLogBook, FFPLUMUlmLogBookAdmin)
