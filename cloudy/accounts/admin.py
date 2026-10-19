import csv

from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.utils.encoding import smart_str
from django.utils.html import format_html, format_html_join

from cloudy.alerts.models import Alert, Qualification
from cloudy.logbooks.models import LogBookBase

from .models import PLAN_CHOICES, UserProfile


def export_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=mymodel.csv"
    writer = csv.writer(response, csv.excel)
    response.write("\ufeff".encode())  # BOM (optional...Excel needs it to open UTF-8 file properly)
    writer.writerow(
        [
            smart_str("Email"),
            smart_str("Prénom"),
            smart_str("Nom"),
            smart_str("Date inscription"),
            smart_str("Date dernière connexion"),
            smart_str("Plan"),
            smart_str("Date de switch"),
            smart_str("Miles balance"),
            smart_str("Month balance"),
        ]
    )
    for obj in queryset:
        plan_switch = obj.fplan_switch_date.strftime("%d / %m / %y") if obj.fplan_switch_date else ""
        writer.writerow(
            [
                smart_str(obj.user.email),
                smart_str(obj.user.first_name),
                smart_str(obj.user.last_name),
                smart_str(obj.user.date_joined.strftime("%d / %m / %y")),
                smart_str(obj.user.last_login.strftime("%d / %m / %y")),
                smart_str(PLAN_CHOICES[int(obj.plan) - 1][1]),
                smart_str(plan_switch),
                smart_str(obj.miles_balance),
                smart_str(obj.month_balance),
            ]
        )
    return response


export_csv.short_description = "Export CSV"


class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "u_email",
        "plan",
        "miles_balance",
        "month_balance",
        "gender",
        "space_balance",
        "logbooks_link",
        "alerts_link",
        "cgv_date",
    )
    list_filter = ("plan", "user__date_joined")
    search_fields = ["user__first_name", "user__last_name", "user__email"]
    readonly_fields = ("cgv_date",)
    actions = [export_csv]

    def u_email(self, obj):
        return "%s" % (obj.user.email)

    def space_balance(self, obj):
        return "%s Kb" % (obj.disk_space_balance / 1000)

    @admin.display(description="Logbooks link")
    def logbooks_link(self, obj):
        link_logbooks = ""
        if LogBookBase.objects.filter(ownr_id=obj.user.id, deleted=False):
            url = reverse(
                "admin_user_logbooks",
                kwargs={
                    "user_id": obj.user.id,
                },
            )
            link_logbooks = format_html("<a href='{}'>logbooks</a>", url)

        if not link_logbooks:
            link_logbooks = "Aucun logbook actif"

        return link_logbooks

    @admin.display(description="Alerts link")
    def alerts_link(self, obj):
        links = []
        qualifications = Qualification.objects.filter(ownr_id=obj.user.id)
        for qualification in qualifications:
            for alert in Alert.objects.filter(qualification_id=qualification.id):
                url = reverse("admin_user_alerts", kwargs={"alert_id": alert.id})
                links.append(format_html("<a href='{}'>alerts_{}</a>", url, alert.id))

        if not links:
            return "Aucune alerte"

        return format_html_join(" ", "{}", ((link,) for link in links))


admin.site.register(UserProfile, UserProfileAdmin)
