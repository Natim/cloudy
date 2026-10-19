from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured

from cloudy.height_format import HEIGHT_FORMAT_CHOICES
from cloudy.height_format.forms import BaseHeightFormattedForm
from cloudy.imports.models import Import
from cloudy.logbooks.models import LogBookBase
from cloudy.time_format import TIME_FORMAT_CHOICES
from cloudy.time_format.forms import BaseTimeFormattedForm


class EditLbookNameForm(forms.Form):
    name = forms.CharField(
        max_length=30,  # According to the model
        label="Nom du carnet",
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )

    time_format = forms.IntegerField(
        label="Format temps", widget=forms.widgets.Select(choices=TIME_FORMAT_CHOICES)
    )

    height_format = forms.IntegerField(
        label="Format hauteur", widget=forms.widgets.Select(choices=HEIGHT_FORMAT_CHOICES)
    )

    def clean(self):
        cleaned_data = self.cleaned_data
        if "name" in cleaned_data:
            if len(cleaned_data["name"]) < 4:
                raise forms.ValidationError("Nom de carnet trop court.")
        return cleaned_data

    def rename(self, logbook, user_id):
        name = self.cleaned_data["name"]
        default_name = LogBookBase.check_unique_name(
            log_book_class=logbook.__class__, user_id=user_id, name=name
        )
        logbook.name = default_name
        logbook.save()


class DeleteLbookForm(forms.Form):
    """
    Delete Logbook form
    """

    should_delete = forms.BooleanField(
        required=False,
        label="Delete",
        help_text="En cochant cette case, je confirme avoir conscience que \
                    l'opération de suppression du carnet est irréversible",
    )

    def delete(self, logbook, user_profile):
        name = "Deleted_%s" % logbook.name
        default_name = LogBookBase.check_unique_name(
            log_book_class=logbook.__class__, user_id=user_profile.user_id, name=name
        )
        logbook.name = default_name
        logbook.deleted = True
        logbook.save()

        # recalculate disk space used
        user_profile.recalc_disk_balance()


class LogForm(BaseTimeFormattedForm, BaseHeightFormattedForm):
    """
    Base Form for a log
    Just a hidden field to detect update from create actions.
    Since we can do both add and edit from the same url endpoint
    /logbook_id/log/ and
    /logbook_id/log/log_id we need to look at this action field
    to find the log_id
    """

    heightfields = {}
    log_id = forms.CharField(widget=forms.HiddenInput(), max_length=40, required=False)


class FileCommentsForm(forms.Form):
    coms = forms.CharField(
        max_length=400,
        required=False,
        label="Commentaires",
        widget=forms.Textarea(attrs={"class": "textarea-custom"}),
    )
    data_file = forms.FileField(
        label="Fichier csv",
        required=True,
    )

    def send_file_to_manager(self, file_to_import, user, logbook):
        coms = self.cleaned_data.get("coms", "")
        owner_email = settings.IMPORT_DEFAULT_OWNER_EMAIL
        if not owner_email:
            raise ImproperlyConfigured(
                "Set IMPORT_DEFAULT_OWNER_EMAIL to the staff user who receives manual imports."
            )
        nimport = Import(
            owner=User.objects.get(email=owner_email),
            import_state=1,
            logbook_state=0,
            user=user,
            logbook=logbook,
            comments=coms,
            file_name=file_to_import.name,
            original_file=file_to_import,
        )
        nimport.save()
        return file_to_import.name


class AutoImportForm(forms.Form):
    data_file = forms.FileField(
        label="Fichier CSV ",
        required=True,
    )

    minutes_only = forms.BooleanField(required=False, label="Temps en minutes ")
