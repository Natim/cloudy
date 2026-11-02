import csv

from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.utils.encoding import smart_str
from django.utils.html import format_html, format_html_join

from cloudy.accounts.impersonation import can_impersonate
from cloudy.alerts.models import Alert, Qualification

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
    change_form_template = "admin/accounts/userprofile/change_form.html"
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

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        profile = self.get_object(request, object_id)
        if profile is not None and can_impersonate(request.user, profile.user):
            extra_context["impersonate_url"] = reverse("impersonate", args=[profile.user_id])
        return super().change_view(request, object_id, form_url, extra_context)

    def u_email(self, obj):
        return "%s" % (obj.user.email)

    def space_balance(self, obj):
        return "%s Kb" % (obj.disk_space_balance / 1000)

    @admin.display(description="Logbooks link")
    def logbooks_link(self, obj):
        active_logbooks = obj.active_logbooks()
        if not active_logbooks:
            return "Aucun logbook actif"

        url = reverse("logbooks:logbook", kwargs={"logbook_id": active_logbooks[0].pk})
        return format_html("<a href='{}'>logbooks</a>", url)

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
