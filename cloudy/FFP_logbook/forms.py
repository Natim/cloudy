from datetime import datetime

from django import forms

from cloudy.FFP_logbook.models import FFPLog
from cloudy.logbooks.forms import LogForm
from cloudy.optional_filter_choices.utils import ffp_optional_filter_choices

# BaseHeightFormattedForm


class FFPReportForm(LogForm):
    timefields = {}
    field_order = [
        "jump_count",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    jump_count = forms.IntegerField(
        label="Nombre de sauts",
        initial=0,
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
    )


COMS_INIT = "Tapez ici vos commentaires"


class FFPLogForm(LogForm):
    heightfields = {
        "altitude": ("hauteur", False),
        "altitude_open": ("Hauteur d'ouverture", False),
    }
    timefields = {}

    def __init__(self, logbook, *args, **kwargs):
        """
        Retrieve the log we want to edit if any
        """
        self.init_log = kwargs.pop("log", None)
        super().__init__(logbook, *args, **kwargs)
        if self.init_log:
            self.initialize_form_fields(self.init_log)

    date = forms.DateField(
        label="Date",
        widget=forms.TextInput(attrs={"class": "input-medium date"}),
        required=True,
    )

    place = forms.CharField(
        label="Lieu",
        max_length=30,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
        required=True,
    )

    aircraft = forms.CharField(
        label="Aéronef",
        max_length=30,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
        required=True,
    )

    falling_time = forms.IntegerField(
        label="Temps de chute",
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
        required=False,
    )

    canopy = forms.CharField(
        label="Voilure", max_length=30, widget=forms.TextInput(attrs={"class": "input-medium"})
    )

    bag = forms.CharField(
        label="Sac harnais",
        max_length=30,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
        required=False,
    )

    perf_exercise = forms.CharField(
        label="Programme du saut",
        max_length=255,
        widget=forms.Textarea(attrs={"class": "observations"}),
        required=False,
    )

    freefall_training = forms.CharField(
        label="Exercise en chute",
        max_length=255,
        widget=forms.Textarea(attrs={"class": "observations"}),
        required=False,
    )

    canopy_piloting = forms.CharField(
        label="Exercise sous voile",
        max_length=255,
        widget=forms.Textarea(attrs={"class": "observations"}),
        required=False,
    )
    # comments
    coms = forms.CharField(
        max_length=400,
        required=False,
        label="Commentaires",
        widget=forms.Textarea(attrs={"class": "observations defaultText", "title": COMS_INIT}),
    )
    media = forms.FileField(
        required=False,
        label="",
    )

    optional_filter = forms.ChoiceField(
        label="Nature du saut", choices=ffp_optional_filter_choices, required=False
    )

    def initialize_form_fields(self, log):
        """
        Use the log instance to prepopulate the form fields
        """
        # flight time
        if log.lbook.height_format_str == "pieds":
            altitude, altitude_open = log.altitude * 3.28084, log.altitude_open * 3.28084
        else:
            altitude, altitude_open = log.altitude, log.altitude_open

        dic = {
            "date": log.date,
            "perf_exercise": log.perf_exercise,
            "freefall_training": log.freefall_training,
            "canopy_piloting": log.canopy_piloting,
            "altitude": altitude,
            "altitude_open": altitude_open,
            "place": log.place,
            "aircraft": log.aircraft,
            "canopy": log.canopy,
            "bag": log.bag,
            "coms": log.cmmts,
            "log_id": log.id,
            "falling_time": log.falling_time,
            "optional_filter": log.optional_filter,
        }
        self.initial = dic

    def clean(self):
        cleaned_data = self.cleaned_data
        return cleaned_data

    def save(self, user, logbook, files, log=None):
        """
        Save log (update or create)
        """
        date_now = datetime.now()
        cleaned_data = self.cleaned_data

        # Create log date
        if log is None:
            cdate = date_now
        else:
            cdate = log.cdate

        # Update date
        d = cleaned_data["date"]
        date = cdate.replace(d.year, d.month, d.day)
        update = date_now

        # clean some fields
        coms = cleaned_data["coms"]
        if coms == COMS_INIT:
            coms = ""

        if not log:
            log = FFPLog()

        log.lbook = logbook
        log.cdate = cdate
        log.update = update
        log.date = date

        log.perf_exercise = cleaned_data["perf_exercise"]
        log.freefall_training = cleaned_data["freefall_training"]
        log.canopy_piloting = cleaned_data["canopy_piloting"]
        log.altitude = cleaned_data["altitude"]
        log.altitude_open = cleaned_data["altitude_open"]
        log.place = cleaned_data["place"]
        log.bag = cleaned_data["bag"]
        log.aircraft = cleaned_data["aircraft"]
        log.canopy = cleaned_data["canopy"]
        falling_time = cleaned_data["falling_time"]
        if not falling_time:
            falling_time = 0
        log.falling_time = falling_time
        log.cmmts = coms

        log.optional_filter = cleaned_data["optional_filter"]
        return log
