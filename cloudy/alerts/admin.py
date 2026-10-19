from django.contrib import admin

from .models import (
    Alert,
    AlertGlissante,
    Qualification,
    QualificationGlissante,
    QualificationGlissanteType,
    QualificationType,
)


class AlertAdmin(admin.ModelAdmin):
    list_filter = ("sent", "kind", "days_before")
    list_display = ("qualification", "kind", "days_before", "sent")


class QualificationTypeAdmin(admin.ModelAdmin):
    list_filter = ("type", "sub_type")
    list_display = ("categ", "type", "sub_type", "name")


class AlertGlissanteAdmin(admin.ModelAdmin):
    list_filter = ("sent",)
    list_display = ("qualif", "sent")


class QualificationGlissanteTypeAdmin(admin.ModelAdmin):
    list_filter = ("category",)
    list_display = ("category", "name")


admin.site.register(QualificationType, QualificationTypeAdmin)
admin.site.register(Qualification)
admin.site.register(Alert, AlertAdmin)
admin.site.register(QualificationGlissanteType, QualificationGlissanteTypeAdmin)
admin.site.register(QualificationGlissante)
admin.site.register(AlertGlissante, AlertGlissanteAdmin)
