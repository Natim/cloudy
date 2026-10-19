from datetime import datetime

from django import forms

from cloudy.core.widgets import HorizontalRadioSelect
from cloudy.DGAC_planeur_logbook.models import (
    DGACPlaneurLog,
    DOUBLE_CDB_INS,
    FUNCTION_ON_BOARD,
    LAUNCH_MODE,
    NATVOL,
)
from cloudy.logbooks.forms import LogForm
from cloudy.optional_filter_choices.utils import optional_filter_choices


class DGACPlaneurReportForm(LogForm):
    """
    Form to report old logbook for DGAC.
    """

    timefields = {
        "flytime_dbl": ("Vols en double", False),
        "flytime_cdb": ("Vols en commandant de bord", False),
        "flytime_ins": ("Vols en instructeur", False),
    }

    def __init__(self, logbook, *args, **kwargs):
        super().__init__(logbook, *args, **kwargs)


OBS_INIT = "Tapez ici les observations"
COMS_INIT = "Tapez ici vos commentaires"


class DGACPlaneurLogForm(LogForm):
    """
    DGAC glider log form
    """

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
    ltype = forms.CharField(
        label="Type",
        max_length=10,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
        required=True,
    )
    imma = forms.CharField(
        label="Immatriculation",
        max_length=10,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )
    fboard = forms.ChoiceField(
        choices=FUNCTION_ON_BOARD, initial="ep", label="Function à bord", required=True
    )
    nvol = forms.ChoiceField(label="Nature du vol", choices=NATVOL, initial="L", required=True)
    lmode = forms.ChoiceField(label="Méthode de lancement", choices=LAUNCH_MODE, initial="R", required=True)
    flight_dci = forms.ChoiceField(
        label="",
        widget=HorizontalRadioSelect(),
        choices=DOUBLE_CDB_INS,
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

    # Landing / Take off
    landingcount = forms.IntegerField(
        label="Décollages",
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
        required=False,
    )

    takeoffcount = forms.IntegerField(
        label="Atterrissages",
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
        required=False,
    )

    optional_filter = forms.ChoiceField(label="Facultatif", choices=optional_filter_choices, required=False)
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
        if log.flytime_ins:
            flight_time = log.flytime_ins
            flight_type = "i"
        dic = {
            "date": log.date,
            "ltype": log.glider_type,
            "imma": log.glider_imma,
            "fboard": log.fctbrd,
            "nvol": log.natvol,
            "lmode": log.lmode,
            "flight_dci": flight_type,
            "flight_time": flight_time,
            "obs": log.obs,
            "aerostart": log.airpdep,
            "aeroend": log.airpar,
            "passengerA": log.staffob,
            "coms": log.cmmts,
            "optional_filter": log.optional_filter,
            # hidden var log_id
            "log_id": log.id,
        }
        self.initial = dic

    def clean(self):
        """
        Clean planeur form
        """
        cleaned_data = self.cleaned_data
        return cleaned_data

    def save(self, user, logbook, files, log=None):
        """
        Save log (update or create)
        """
        date_now = datetime.now()
        cleaned_data = self.cleaned_data
        flight_dci = cleaned_data.get("flight_dci")
        flight_time = cleaned_data.get("flight_time")

        # flytime
        flytime_cdb = flytime_dbl = flytime_ins = 0
        if flight_dci == "c":
            flytime_cdb = flight_time
        if flight_dci == "d":
            flytime_dbl = flight_time
        if flight_dci == "i":
            flytime_ins = flight_time

        # date
        # Create log
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
        obs = cleaned_data["obs"]
        if obs == OBS_INIT:
            obs = ""

        # staffob is a string with name separated by ';'
        # staffob =  ";".join([cleaned_data['passengerA'],])
        staffob = cleaned_data["passengerA"]

        if not log:
            log = DGACPlaneurLog()

        log.lbook = logbook
        log.cdate = cdate
        log.update = update
        log.date = date
        log.glider_type = cleaned_data["ltype"]
        log.glider_imma = cleaned_data["imma"]
        log.fctbrd = cleaned_data["fboard"]
        log.natvol = cleaned_data["nvol"]
        log.lmode = cleaned_data["lmode"]
        log.flytime_cdb = flytime_cdb
        log.flytime_dbl = flytime_dbl
        log.flytime_ins = flytime_ins
        log.optional_filter = cleaned_data["optional_filter"]

        log.obs = obs
        log.airpdep = cleaned_data["aerostart"]
        log.airpar = cleaned_data["aeroend"]
        log.staffob = staffob
        log.cmmts = coms

        return log
