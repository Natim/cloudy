from datetime import datetime

from django import forms
from django.forms.utils import ErrorList

from cloudy.core.widgets import HorizontalRadioSelect
from cloudy.FCL1080.models import FCL1080Log
from cloudy.logbooks.forms import LogForm
from cloudy.logbooks.icao import icao_from_place
from cloudy.time_format.widgets import HhmmField, HhmmWidget


class FCL1080ReportForm(LogForm):
    """
    Form to report old logbook for DGAC.
    """

    timefields = {
        "single_pilot_time": ("Durée mono pilote", False),
        "multi_pilot_time": ("Durée multi pilote", False),
        "total_time_flight": ("Total général", False),
        "op_time_night": ("Durée en condition opérationnelle de nuit", False),
        "op_time_ifr": ("Durée en condition opérationnelle IFR", False),
        "pilot_time_in_cmd": ("Commandant de bord", False),
        "pilot_timpe_cop": ("Co-pilote", False),
        "pilot_time_dual": ("Double commande", False),
        "pilot_time_inst": ("Instructeur", False),
        "synthetic_time": ("Heures totales (Simulateur de vol)", False),
    }

    field_order = [
        "single_pilot_time",
        "multi_pilot_time",
        "total_time_flight",
        "op_time_night",
        "op_time_ifr",
        "pilot_time_in_cmd",
        "pilot_timpe_cop",
        "pilot_time_dual",
        "pilot_time_inst",
        "synthetic_time",
        "take_off_day",
        "take_off_night",
        "landing_day",
        "landing_night",
    ]

    def __init__(self, logbook, *args, **kwargs):
        super().__init__(logbook, *args, **kwargs)

    take_off_day = forms.IntegerField(
        label="Nombre de décollage de jours",
        initial=0,
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
    )

    take_off_night = forms.IntegerField(
        label="Nombre de décollage de nuit",
        initial=0,
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
    )

    landing_day = forms.IntegerField(
        label="Nombre d'atterrissage de jour",
        initial=0,
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
    )

    landing_night = forms.IntegerField(
        label="Nombre d'atterrissage de nuit",
        initial=0,
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
    )


OBS_INIT = "Tapez ici les observations"
COMS_INIT = "Tapez ici vos commentaires"

# some fields do not need pre processing to# saved to model
MAPPED_FIELDS = [
    "departure_place",
    "departure_time",
    "arrival_place",
    "arrival_time",
    "aircraft_type",
    "aircraft_imma",
    "single_pilot_time",
    "multi_pilot_time",
    "total_time_flight",
    "name_pic",
    "take_off_day",
    "take_off_night",
    "landing_day",
    "landing_night",
    "op_time_night",
    "op_time_ifr",
    "pilot_time_in_cmd",
    "pilot_timpe_cop",
    "pilot_time_dual",
    "pilot_time_inst",
    "synthetic_date",
    "synthetic_type",
    "synthetic_time",
]


class FCL1080LogForm(LogForm):
    """
    FCL 1080 LogForm
    """

    timefields = {
        "single_pilot_time": ("Single-pilot time", False),
        "multi_pilot_time": ("Multi-pilot time", False),
        "total_time_flight": ("Total time of flight", False),
        "op_time_night": ("Night time", False),
        "op_time_ifr": ("IFR time", False),
        "pilot_time_in_cmd": ("Pilot in command", False),
        "pilot_timpe_cop": ("Co-pilot", False),
        "pilot_time_dual": ("Dual", False),
        "pilot_time_inst": ("Instructor", False),
        "synthetic_time": ("Total session time", False),
    }

    def __init__(self, *args, **kwargs):
        """
        Retrieve the log we want to edit if any
        """
        self.init_log = kwargs.pop("log", None)
        super().__init__(*args, **kwargs)
        # synthetic ?
        self.is_synt = False
        if self.init_log:
            self.initialize_form_fields(self.init_log)

    departure_time = HhmmField(required=False, label="Departure time", widget=HhmmWidget())
    arrival_time = HhmmField(required=False, label="Arrival time", widget=HhmmWidget())

    date = forms.DateField(
        required=False,
        label="Date",
        widget=forms.TextInput(attrs={"class": "input-medium date"}),
    )
    departure_place = forms.CharField(
        required=False,
        label="Departure place",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )

    arrival_place = forms.CharField(
        required=False,
        label="Arrival place",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )

    aircraft_type = forms.CharField(
        required=False,
        label="Make Model Variant",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )
    aircraft_imma = forms.CharField(
        required=False,
        label="Registration",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )

    single_pilot_se_me = forms.ChoiceField(
        required=False,
        # coerce=lambda x: bool(int(x)),
        choices=((0, "SE"), (1, "ME"), (-1, "Aucun")),
        widget=HorizontalRadioSelect(),
    )

    name_pic = forms.CharField(
        label="Name pic",
        max_length=30,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
        required=False,
    )

    take_off_day = forms.IntegerField(
        label="Takeoffs Day",
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
        required=False,
    )
    take_off_night = forms.IntegerField(
        label="Takeoffs Night",
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
        required=False,
    )
    landing_day = forms.IntegerField(
        label="Landings Day",
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
        required=False,
    )
    landing_night = forms.IntegerField(
        label="Landings Night",
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
        required=False,
    )

    # Synth.
    synthetic_date = forms.DateField(
        label="Date", widget=forms.TextInput(attrs={"class": "input-medium date"}), required=False
    )
    synthetic_type = forms.CharField(
        label="Type",
        max_length=30,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
        required=False,
    )

    # Passengers
    passengerA = forms.CharField(
        label="Personne A",
        required=False,
        max_length=30,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )
    passengerB = forms.CharField(
        label="Personne B",
        required=False,
        max_length=30,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )
    passengerC = forms.CharField(
        label="Personne C",
        required=False,
        max_length=30,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )

    # Obs
    obs = forms.CharField(
        max_length=200,
        label="Remarks and endorsements",
        widget=forms.Textarea(attrs={"class": "observations defaultText"}),
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

    def clean(self):
        """
        Validation RULE
        If synthetic_date and synthetic_type and synthetic_time are filled and valid
        we do not need to have

        ['departure_place', 'departure_time', 'arrival_place', 'arrival_time', \
          'aircraft_type', 'aircraft_imma', 'single_pilot_time', 'multi_pilot_time', 'total_time_flight'] Filled
        """
        synthetic_date = self.cleaned_data.get("synthetic_date", None)
        synthetic_type = self.cleaned_data.get("synthetic_type", None)
        synthetic_time = self.cleaned_data.get("synthetic_time", None)

        date = self.cleaned_data.get("date", None)
        departure_place = self.cleaned_data.get("departure_place", None)
        departure_time = self.cleaned_data.get("departure_time", None)
        arrival_place = self.cleaned_data.get("arrival_place", None)
        arrival_time = self.cleaned_data.get("arrival_time", None)
        aircraft_type = self.cleaned_data.get("aircraft_type", None)
        aircraft_imma = self.cleaned_data.get("aircraft_imma", None)
        single_pilot_se_me = self.cleaned_data.get("single_pilot_se_me", None)
        is_synthetic = synthetic_date and synthetic_type and synthetic_time
        if not is_synthetic:
            error_missing_field = ErrorList(["Le champs est obligatoire"])
            if not date:
                self._errors["date"] = error_missing_field
            if not departure_place:
                self._errors["departure_place"] = error_missing_field
            if not departure_time:
                self._errors["departure_time"] = error_missing_field
            if not arrival_place:
                self._errors["arrival_place"] = error_missing_field
            if not arrival_time:
                self._errors["arrival_time"] = error_missing_field
            if not aircraft_type:
                self._errors["aircraft_type"] = error_missing_field
            if not aircraft_imma:
                self._errors["aircraft_imma"] = error_missing_field
            if not single_pilot_se_me:
                self._errors["single_pilot_se_me"] = error_missing_field

        if is_synthetic and not date:
            self.cleaned_data["date"] = synthetic_date

        cleaned_data = self.cleaned_data
        return cleaned_data

    def initialize_form_fields(self, log):
        """
        Use the log instance to prepopulate the form fields
        """
        # SE ME ?
        single_pilot_se_me = "-1"
        if log.single_pilot_se:
            single_pilot_se_me = "0"
        if log.single_pilot_me:
            single_pilot_se_me = "1"
        list_staff = ["", "", ""]
        try:
            list_staff_split = log.staffob.split(";")
            size_list_staff = len(list_staff)
            for idx, name_staff in enumerate(list_staff_split):
                if idx < size_list_staff:
                    list_staff[idx] = name_staff
        except ValueError:
            staffobA, staffobB, staffobC = "", "", ""
        dic = {
            "date": log.date,
            "passengerA": list_staff[0],
            "passengerB": list_staff[1],
            "passengerC": list_staff[2],
            "single_pilot_se_me": single_pilot_se_me,
            "optional_filter": log.optional_filter,
            "coms": log.cmmts,
            "obs": log.obs,
            # hidden var log_id
            "log_id": log.id,
        }
        for field in MAPPED_FIELDS:
            dic.update({field: getattr(log, field)})

        self.initial = dic
        # media

    def clean_departure_place(self):
        return icao_from_place(self.cleaned_data.get("departure_place"))

    def clean_arrival_place(self):
        return icao_from_place(self.cleaned_data.get("arrival_place"))

    def save(self, user, logbook, files, log=None):
        """
        Save log (update or create)
        """
        date_now = datetime.now()
        cleaned_data = self.cleaned_data

        # Create log
        if log is None:
            cdate = date_now
        else:
            cdate = log.cdate

        # Update date
        d = cleaned_data["date"]
        date = cdate.replace(d.year, d.month, d.day)
        update = date_now

        # clean/pre process some fields
        coms = cleaned_data["coms"]
        if coms == COMS_INIT:
            coms = ""
        obs = cleaned_data["obs"]
        if obs == OBS_INIT:
            obs = ""

        # staffob is a string with name separated by ';'
        staffob = ";".join(
            [
                cleaned_data["passengerA"],
                cleaned_data["passengerB"],
                cleaned_data["passengerC"],
            ]
        )

        if not log:
            log = FCL1080Log()
        log.lbook = logbook
        log.cdate = cdate
        log.update = update
        log.date = date
        log.airpdep = cleaned_data["departure_place"]
        log.airpar = cleaned_data["arrival_place"]
        for field in MAPPED_FIELDS:
            setattr(log, field, cleaned_data[field])
        se_choice = cleaned_data["single_pilot_se_me"]
        if se_choice == "0":
            log.single_pilot_se = True
            log.single_pilot_me = False
        elif se_choice == "1":
            log.single_pilot_me = True
            log.single_pilot_se = False
        elif se_choice == "-1":
            log.single_pilot_se = False
            log.single_pilot_me = False

        log.obs = obs
        log.staffob = staffob
        log.cmmts = coms

        return log
