from datetime import datetime

from django import forms

from cloudy.core.widgets import HorizontalRadioSelect
from cloudy.FFPLUM_ulm_logbook.models import DOUBLE_CDB, FFPLUMUlmLog
from cloudy.logbooks.forms import LogForm
from cloudy.optional_filter_choices.utils import optional_filter_choices


class FFPLUMUlmReportForm(LogForm):
    """
    Report form for ULM
    """

    timefields = {
        "flytime_dbl": ("Vols en double", False),
        "flytime_cdb": ("Vols en commandant de bord", False),
    }
    field_order = [
        "flytime_dbl",
        "flytime_cdb",
        "nbrto",
        "nbrla",
    ]

    def __init__(self, logbook, *args, **kwargs):
        super().__init__(logbook, *args, **kwargs)

    nbrto = forms.IntegerField(
        label="Nombre de décollage",
        initial=0,
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
    )

    nbrla = forms.IntegerField(
        label="Nombre d'atterrissage",
        initial=0,
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
    )


OBS_INIT = "Tapez ici les observations"
COMS_INIT = "Tapez ici vos commentaires"


class FFPLUMUlmLogForm(LogForm):
    timefields = {
        "flight_time": ("Temps de vol", True),
    }

    def __init__(self, logbook, *args, **kwargs):
        """
        Retrieve the log we want to edit if any
        """
        self.init_log = kwargs.pop("log", None)
        super().__init__(logbook, *args, **kwargs)

        if self.init_log:
            self.initialize_form_fields(self.init_log)

    date = forms.DateField(
        label="Date", widget=forms.TextInput(attrs={"class": "input-medium date"}), required=True
    )
    ulm_type = forms.CharField(
        label="Type",
        max_length=10,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
        required=True,
    )
    ulm_imma = forms.CharField(
        label="Immatriculation",
        max_length=10,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )

    flight_dc = forms.ChoiceField(
        label="",
        widget=HorizontalRadioSelect(),
        choices=DOUBLE_CDB,
        initial="c",
        required=True,
    )

    # Non required fields
    # Obs
    obs = forms.CharField(
        max_length=200,
        label="Observations",
        widget=forms.Textarea(attrs={"class": "observations defaultText", "title": OBS_INIT}),
        required=False,
    )

    optional_filter = forms.ChoiceField(label="Facultatif", choices=optional_filter_choices, required=False)
    # Landing / Take off
    takeoffcount = forms.IntegerField(
        label="Décollages",
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
        required=False,
    )

    landingcount = forms.IntegerField(
        label="Atterrissages",
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
        required=False,
    )

    # aeroport
    aerostart = forms.CharField(
        label="Zone de vol de départ",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )

    aeroend = forms.CharField(
        label="Zone de vol d'arrivée",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )

    # Passengers
    passengerA = forms.CharField(
        label="Personne A",
        required=False,
        max_length=30,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
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

    def initialize_form_fields(self, log):
        """
        Use the log instance to prepopulate the form fields
        """
        # flight time
        flight_time = 0
        flight_type = ""
        if log.flytime_cdb:
            flight_time = log.flytime_cdb
            flight_type = "c"
        if log.flytime_dbl:
            flight_time = log.flytime_dbl
            flight_type = "d"

        dic = {
            "date": log.date,
            "ulm_type": log.ulm_type,
            "ulm_imma": log.ulm_imma,
            "flight_dc": flight_type,
            "flight_time": flight_time,
            "obs": log.obs,
            "aerostart": log.airpdep,
            "aeroend": log.airpar,
            "passengerA": log.staffob,
            "coms": log.cmmts,
            "landingcount": log.nbrla,
            "takeoffcount": log.nbrto,
            "log_id": log.id,
            "optional_filter": log.optional_filter,
        }
        self.initial = dic

    def clean(self):
        """
        Clean ULM form
        """
        cleaned_data = self.cleaned_data
        return cleaned_data

    def save(self, user, logbook, files, log=None):
        """
        Save log (update or create)
        """
        date_now = datetime.now()
        cleaned_data = self.cleaned_data
        flight_dc = cleaned_data.get("flight_dc")
        flight_time = cleaned_data.get("flight_time")

        # flytime
        flytime_cdb = flytime_dbl = 0
        if flight_dc == "c":
            flytime_cdb = flight_time
        if flight_dc == "d":
            flytime_dbl = flight_time

        # Create log
        cdate = date_now if log is None else log.cdate

        # Update date
        d = cleaned_data["date"]
        date = cdate.replace(d.year, d.month, d.day)
        update = date_now

        # clean some fields
        coms = cleaned_data["coms"]
        if coms == COMS_INIT:
            coms = ""
        obs = cleaned_data["obs"]
        if obs == OBS_INIT:
            obs = ""

        nbrto = cleaned_data["takeoffcount"]
        if not nbrto:
            nbrto = 0
        nbrla = cleaned_data["landingcount"]
        if not nbrla:
            nbrla = 0  # staffob is a string with name separated by ';'
        # staffob =  ";".join([cleaned_data['passengerA'],])
        staffob = cleaned_data["passengerA"]

        if not log:
            log = FFPLUMUlmLog()

        log.lbook = logbook
        log.cdate = cdate
        log.update = update
        log.date = date
        log.ulm_type = cleaned_data["ulm_type"]
        log.ulm_imma = cleaned_data["ulm_imma"]
        log.nbrla = nbrla
        log.nbrto = nbrto
        log.flytime_cdb = flytime_cdb
        log.flytime_dbl = flytime_dbl
        log.optional_filter = cleaned_data["optional_filter"]

        log.obs = obs
        log.airpdep = cleaned_data["aerostart"]
        log.airpar = cleaned_data["aeroend"]
        log.staffob = staffob
        log.cmmts = coms

        return log
