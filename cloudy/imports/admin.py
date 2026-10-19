# System imports {{{
import pathlib
import tempfile

from django import forms

# }}}
# Django imports {{{
from django.contrib import admin, messages
from django.core.mail import send_mail
from django.template.loader import render_to_string

from cloudy.logbooks.models import LogBookBase

# }}}
# Cloudy {{{
from .models import Import

# }}}


class ImportForm(forms.ModelForm):
    csv_file = forms.FileField(
        label="Fichier xls/csv",
        required=False,
    )

    class Meta:
        model = Import
        fields = "__all__"


class ImportAdmin(admin.ModelAdmin):
    form = ImportForm

    # Fields display parameters {{{
    list_display = (
        "owner",
        "import_state",
        "logbook_state",
        "user",
        "type",
        "logbook",
        "minutes_only",
        "comments",
        "notification_delivered",
    )
    list_display_links = ("owner", "user", "logbook")
    list_editable = (
        "import_state",
        "logbook_state",
        "minutes_only",
    )
    list_filter = (
        "import_state",
        "logbook_state",
        "owner",
        "notification_delivered",
    )
    readonly_fields = (
        "notification_delivered",
        "logbook",
        "user",
    )
    exclude = ("file_name",)
    # }}}

    def save_model(self, request, obj, form, change):
        f = request.FILES.get("csv_file", None)
        if f == None:
            return obj.save()

        # Store the file to a temporary place.
        output = tempfile.NamedTemporaryFile(delete=False)
        output_path = output.name
        destination = pathlib.Path(output_path).open("wb+")
        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()

        # Grab the correct logbook.
        logbook = LogBookBase.get_by_id(obj.logbook.pk)

        # Import the CSV.
        tim = form.cleaned_data["minutes_only"]
        result = logbook.import_from_csv(output_path, delimiter=";", time_in_min=tim)

        # Tell the user if everything went well
        if result["success"] == True:
            messages.info(request, "Logbook successfully imported. (%s logs)" % result["count"])
            obj.logbook_state = 2

            # If we want to, send the e-mail notification.
            if form.cleaned_data["send_notification"] == True:
                body_html = render_to_string(
                    "mails/import/import_done.html", {"full_name": logbook.ownr.get_full_name()}
                )
                subject = render_to_string("mails/import/import_done_subject.html", {})
                subject = subject.replace("\n", "")
                send_mail(subject, body_html, "support@cloudy.fr", [logbook.ownr.email])
                obj.notification_delivered = True

            obj.save()

        else:
            messages.error(request, "The following error happened: %s." % result["message"])

        return False


admin.site.register(Import, ImportAdmin)
