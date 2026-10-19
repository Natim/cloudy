from django.contrib import admin

from .models import FfpOptionalFilterChoice, OptionalFilterChoice


class OptionalFilterChoiceAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name")
    fields = ("short_name", "name")


class FfpOptionalFilterChoiceAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name")
    fields = ("short_name", "name")


admin.site.register(OptionalFilterChoice, OptionalFilterChoiceAdmin)
admin.site.register(FfpOptionalFilterChoice, FfpOptionalFilterChoiceAdmin)
