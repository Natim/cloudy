from datetime import datetime

from django import forms
from django.forms.widgets import SelectDateWidget

from .models import (
    Alert,
    Qualification,
    QUALIFICATION_GLISSANTE_SUB_TYPES,
    QualificationGlissante,
    QualificationType,
)

ALERT_BEFORE = (
    (1, "1 jour"),
    (2, "2 jours"),
    (3, "3 jours"),
    (7, "1 semaine"),
    (14, "2 semaines"),
    (30, "1 mois"),
    (60, "2 mois"),
    (90, "3 mois"),
)


class QualificationForm(forms.ModelForm):
    """
    Qualifications changes.
    """

    field_order = [
        "ownr",
        "qualif_uid",
        "achievement_date",
        "expiry_date",
        "alert_days_before",
        "sms_alert",
        "email_alert",
        "photo",
    ]

    def __init__(self, *args, owner=None, **kw):
        self._owner = owner
        super().__init__(*args, **kw)

    qualif_uid = forms.CharField(
        required=True,
        widget=forms.HiddenInput,
    )

    achievement_date = forms.DateField(
        required=True,
        widget=SelectDateWidget(years=range(datetime.today().year, datetime.today().year - 50, -1)),
        label="Date d'obtention",
    )

    expiry_date = forms.DateField(
        widget=SelectDateWidget(years=range(datetime.today().year + 50, datetime.today().year - 1, -1)),
        label="Date d'expiration",
        required=False,
    )

    alert_days_before = forms.IntegerField(
        widget=forms.Select(choices=ALERT_BEFORE),
        label="Être alerté avant",
        help_text="Jours / semaines / mois",
    )

    sms_alert = forms.BooleanField(
        required=False,
        initial=False,
        label="SMS",
        help_text="Recevoir une alerte par SMS",
    )

    email_alert = forms.BooleanField(
        required=False,
        initial=True,
        label="Email",
        help_text="Recevoir une alerte par email",
    )

    photo = forms.ImageField(
        required=False, label="Image / Document", help_text="Scan / photo de la qualification"
    )

    class Meta:
        model = Qualification
        exclude = ("license_type", "ownr")

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self._owner is not None:
            instance.ownr = self._owner

        qtype = QualificationType.objects.get(pk=self.cleaned_data["qualif_uid"])

        instance.license_type = qtype
        instance.save()

        # Create the alerts.
        # We erase the old ones, if any.
        for old_alert in instance.alert_set.all():
            old_alert.delete()
        for kind in ["sms", "email"]:
            if self.cleaned_data["%s_alert" % kind]:
                params = {
                    "qualification": instance,
                    "kind": kind,
                    "days_before": self.cleaned_data["alert_days_before"],
                }
                Alert(**params).save()

        # Do the save job.
        # Actually it's wrong: we already saved the instance anyway, because we
        # need a PK to store the alert foreign keys.
        if commit:
            instance.save()

        return instance


class QualificationGlissanteForm(forms.ModelForm):
    """
    Qualifications Glissantes changes.
    """

    subtype = forms.ChoiceField(
        required=True,
        label="Certification",
        widget=forms.Select(),
        choices=QUALIFICATION_GLISSANTE_SUB_TYPES,
    )

    qtype = forms.CharField(
        required=True,
        label="QType",
    )

    logbook_name = forms.CharField(
        required=True,
        label="Logbook",
    )

    experience_int = forms.IntegerField(required=True, label="Expérience / Utilisation")

    experience_unity = forms.ChoiceField(
        required=True, choices=(("heure de vol", "Heure de vol"), ("vol", "Vol"))
    )

    duree_int = forms.IntegerField(
        required=True,
        label="Dans les",
        help_text='Saisir "99 année" pour considérer une période illimitée.',
    )

    duree_unity = forms.ChoiceField(
        required=True, choices=(("jour", "Jour"), ("mois", "Mois"), ("annee", "Année"))
    )

    class Meta:
        model = QualificationGlissante
        exclude = ("ownr", "license_type", "loogbook")
