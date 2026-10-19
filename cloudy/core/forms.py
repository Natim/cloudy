import pathlib
import random
import string
import tempfile
from datetime import datetime

from django import forms
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.management import CommandError
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from cloudy.core.widgets import MultiEmailField
from cloudy.logbooks.settings import MAP


class MultiMailInvitationForm(forms.Form):
    """Email share form"""

    emails = MultiEmailField(
        widget=forms.Textarea(attrs={"class": "textarea-custom"}),
        help_text=_("Example: flagadajohnes@gmail.com, robinolds@yahoo.com"),
    )

    def send_invites(self, from_user, sponsored_link):
        """Send mails"""
        emails = self.cleaned_data["emails"]

        subject_txt = render_to_string(
            "mails/referral_invitation/email_subject.txt",
            {
                "from_user": from_user,
            },
        )

        body_txt = render_to_string(
            "mails/referral_invitation/email_body.txt",
            {
                "from_user": from_user,
                "sponsored_link": sponsored_link,
            },
        )
        send_mail(subject_txt.replace("\n", ""), body_txt, "contact@cloudy.fr", emails)


BOOK_CHOICES = (
    ("plane_dgac", "plane_dgac"),
    ("glider_dgac", "glider_dgac"),
    ("ulm_ffplum", "ulm_ffplum"),
)


class ImportLogbookForm(forms.Form):
    """Form for importing a logbook"""

    user_id = forms.CharField(required=True)
    aeronef_type = forms.ChoiceField(required=True, choices=BOOK_CHOICES)
    logbook_id = forms.CharField(max_length=30, required=False)
    data_file = forms.FileField(
        label="Fichier xls/csv",
        required=True,
    )
    time_in_min = forms.BooleanField(label="are time strings in minutes ?", required=False)

    @property
    def user_choices(self):
        return [(u.id, f"{u.id} - {u.get_full_name()}") for u in User.objects.all()]

    def import_csv(self, file_to_import):
        """
        Do import
        """
        logbook_id = self.cleaned_data["logbook_id"]
        class_name = self.cleaned_data["aeronef_type"]
        user_id = self.cleaned_data["user_id"]
        user = User.objects.get(pk=user_id)

        output = tempfile.NamedTemporaryFile(delete=False)
        output_path = output.name

        self.handle_uploaded_file(file_to_import, output_path)

        klass = MAP[class_name]

        if logbook_id != "":
            try:
                logbook = klass.objects.get(id=logbook_id)
            except klass.DoesNotExist:
                raise CommandError("Logbook does not exist")
        else:
            random_str = "".join(random.choice(string.letters) for i in range(1, 5))
            logbook = klass(name="import_%s" % (random_str), ownr=user, cdate=datetime.now(), cat=class_name)
            logbook.save()

        tim = self.cleaned_data["time_in_min"]
        result = logbook.import_from_csv(output_path, delimiter=";", time_in_min=tim)
        if logbook:
            result["logbook_id"] = str(logbook.id)
        logbook.save()
        return result

    def handle_uploaded_file(self, f, path):
        destination = pathlib.Path(path).open("wb+")
        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()
