from datetime import datetime

from django import forms

from cloudy.DGAC_avion_logbook.models import DGACAvionLog
from cloudy.logbooks.forms import LogForm
from cloudy.optional_filter_choices.utils import optional_filter_choices

FUNCTION_ON_BOARD = (
    ("EP", "Elève Pilote"),
    ("Cdb", "Commandant de bord"),
    ("Pilote", "Pilote"),
    ("Co-pilote", "Co-pilote"),
    ("Inst", "Instructeur"),
    ("Exam", "Examinateur"),
)

DAY_NIGHT = (("d", "Jour"), ("n", "Nuit"))
DOUBLE_CDT = (("d", "Double commande"), ("c", "Cdt de bord"))

DOUBLE_CDT_COP = (("d", "Double commande"), ("c", "Cdt de bord"), ("co", "Co-pilote"))


class DGACAvionReportForm(LogForm):
    """
    Form to report old logbook for DGAC.
    """

    timefields = {
        "mbr_equipage_jour": ("Membre de l'équipage de jour", False),
        "mbr_equipage_nuit": ("Membre de l'équipage de nuit", False),
        "mono_jdbl": ("Pilote monomoteur en double de jour", False),
        "mono_jcdb": ("Pilote monomoteur en commandant de bord de jour", False),
        "mono_ndbl": ("Pilote monomoteur en double de nuit", False),
        "mono_ncdb": ("Pilote monomoteur en commandant de bord de nuit", False),
        "mul_jdbl": ("Pilote multimoteurs en double de jour", False),
        "mul_jcdb": ("Pilote multimoteurs en commandant de bord de jour", False),
        "mul_jcplt": ("Pilote multimoteurs en co-pilote de jour", False),
        "mul_ndbl": ("Pilote multimoteurs en double de nuit", False),
        "mul_ncdb": ("Pilote multimoteurs en commandant de bord de nuit", False),
        "mul_ncplt": ("Pilote multimoteurs en co-pilote de nuit", False),
        "vai_dbl": ("Vol aux instruments en double", False),
        "vai_plt": ("Vol aux instruments en pilote", False),
        "simu": ("Simulation", False),
    }

    field_order = [
        "mbr_equipage_jour",
        "mbr_equipage_nuit",
        "mono_jdbl",
        "mono_jcdb",
        "mono_ndbl",
        "mono_ncdb",
        "mul_jdbl",
        "mul_jcdb",
        "mul_jcplt",
        "mul_ndbl",
        "mul_ncdb",
        "mul_ncplt",
        "vai_dbl",
        "vai_plt",
        "simu",
        "ifr",
        "nbrto",
        "nbrla",
    ]

    def __init__(self, logbook, *args, **kwargs):
        super().__init__(logbook, *args, **kwargs)

    ifr = forms.IntegerField(
        label="IFR",
        initial=0,
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
    )

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


class DGACAvionLogForm(LogForm):
    """
    DGAC avion log form
    """

    timefields = {
        "mbreqtime": ("Temps de vol", False),
        "pmonotime": ("Temps de vol", False),
        "pmultime": ("Temps de vol", False),
        "vaitime": ("Temps de vol", False),
        "simu": ("Simulation", False),
    }

    def __init__(self, logbook, *args, **kwargs):
        """
        Retrieve the log we want to edit if any
        """
        self.init_log = kwargs.pop("log", None)
        super().__init__(logbook, *args, **kwargs)

        if self.init_log:
            self.initialize_form_fields(self.init_log)

    date = forms.DateField(label="Date", widget=forms.TextInput(attrs={"class": "input-medium date"}))
    ltype = forms.CharField(
        label="Type", max_length=10, widget=forms.TextInput(attrs={"class": "input-medium"})
    )
    imma = forms.CharField(
        label="Immatriculation",
        max_length=10,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )
    fboard = forms.ChoiceField(
        choices=FUNCTION_ON_BOARD,
        initial="ep",
        label="Function à bord",
    )
    nvol = forms.CharField(
        label="Nature du vol",
        widget=forms.TextInput(attrs={"class": "input-medium"}),
        max_length=30,
    )

    # Membre equipage dn
    mbreqdn = forms.ChoiceField(
        label="",
        # widget=forms.RadioSelect(renderer=HorizRadioRenderer),# TODO
        widget=forms.RadioSelect(),
        choices=DAY_NIGHT,
        required=False,
    )

    # mbreqtime

    # Pilote mono engine day or night
    pmonodn = forms.ChoiceField(
        label="",
        # widget=forms.RadioSelect(renderer=HorizRadioRenderer),# TODO
        widget=forms.RadioSelect(),
        choices=DAY_NIGHT,
        required=False,
    )
    pmonopos = forms.ChoiceField(
        label="",
        # widget=forms.RadioSelect(renderer=HorizRadioRenderer),# TODO
        widget=forms.RadioSelect(),
        choices=DOUBLE_CDT,
        required=False,
    )

    # pmonotime

    # Pilote mul
    pmuldn = forms.ChoiceField(
        label="",
        # widget=forms.RadioSelect(renderer=HorizRadioRenderer),# TODO
        widget=forms.RadioSelect(),
        choices=DAY_NIGHT,
        required=False,
    )
    pmulpos = forms.ChoiceField(
        label="",
        # widget=forms.RadioSelect(renderer=HorizRadioRenderer),# TODO
        widget=forms.RadioSelect(),
        choices=DOUBLE_CDT_COP,
        required=False,
    )

    # pmultime

    # VAI
    vaipos = forms.ChoiceField(
        label="",
        # widget=forms.RadioSelect(renderer=HorizRadioRenderer),# TODO
        widget=forms.RadioSelect(),
        choices=DOUBLE_CDT,
        required=False,
    )

    # vaitime

    # SIMU
    ifr = forms.IntegerField(
        label="Arrivées I.F.R",
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
        initial=0,
        required=False,
    )

    # Obs
    obs = forms.CharField(
        max_length=200,
        label="Observations",
        widget=forms.Textarea(attrs={"class": "observations defaultText", "title": OBS_INIT}),
        required=False,
    )

    # Landing / Take off
    optional_filter = forms.ChoiceField(label="Facultatif", choices=optional_filter_choices, required=False)

    landingcount = forms.IntegerField(
        label="Atterrissages",
        widget=forms.TextInput(attrs={"class": "input-small"}),
        min_value=0,
        required=False,
    )

    takeoffcount = forms.IntegerField(
        label="Décollages",
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
        Oh god how could we shorten this stuff ? model to form with
        complex radio :/
        """
        # Update mbr equipage
        mbreqdn = ""
        mbreqtime = ""
        if log.mbr_equipage_jour:
            mbreqdn = "d"
            mbreqtime = log.mbr_equipage_jour
        if log.mbr_equipage_nuit:
            mbreqdn = "n"
            mbreqtime = log.mbr_equipage_nuit
        # pilot mono
        # pos 0: pmonodn
        # pos 1: pmonopos
        # pos 2: pmonotime
        pmono_values = ["", "", ""]
        if log.mono_jdbl:
            pmono_values = ["d", "d", log.mono_jdbl]
        if log.mono_ndbl:
            pmono_values = ["n", "d", log.mono_ndbl]
        if log.mono_jcdb:
            pmono_values = ["d", "c", log.mono_jcdb]
        if log.mono_ncdb:
            pmono_values = ["n", "c", log.mono_ncdb]

        # pilot multi
        pmulti_values = ["", "", ""]
        # pos 0: pmuldn
        # pos 1: pmulpos
        # pos 2: pmultime
        if log.mul_jdbl:
            pmulti_values = ["d", "d", log.mul_jdbl]
        if log.mul_jcdb:
            pmulti_values = ["d", "c", log.mul_jcdb]
        if log.mul_jcplt:
            pmulti_values = ["d", "co", log.mul_jcplt]
        if log.mul_ndbl:
            pmulti_values = ["n", "d", log.mul_ndbl]
        if log.mul_ncdb:
            pmulti_values = ["n", "c", log.mul_ncdb]
        if log.mul_ncplt:
            pmulti_values = ["n", "co", log.mul_ncplt]

        vaipos = ["", ""]
        if log.vai_dbl:
            vaipos = ["d", log.vai_dbl]
        if log.vai_plt:
            vaipos = ["c", log.vai_plt]

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
            "ltype": log.aeronef_type,
            "imma": log.aeronef_imma,
            "fboard": log.fctbrd,
            "nvol": log.natvol,
            "mbreqdn": mbreqdn,
            "mbreqtime": mbreqtime,
            "pmonodn": pmono_values[0],
            "pmonopos": pmono_values[1],
            "pmonotime": pmono_values[2],
            "pmuldn": pmulti_values[0],
            "pmulpos": pmulti_values[1],
            "pmultime": pmulti_values[2],
            "vaipos": vaipos[0],
            "vaitime": vaipos[1],
            "simu": log.simu,
            "ifr": log.ifr,
            "obs": log.obs,
            "landingcount": log.nbrla,
            "takeoffcount": log.nbrto,
            "aerostart": log.airpdep,
            "aeroend": log.airpar,
            "passengerA": list_staff[0],
            "passengerB": list_staff[1],
            "passengerC": list_staff[2],
            "optional_filter": log.optional_filter,
            "coms": log.cmmts,
            # hidden var log_id
            "log_id": log.id,
        }

        self.initial = dic
        # media

    def clean(self):
        """
        Rules:
        If mrb equipage or VOI or SIMU is filled we don't need pilote mono or pilote multi.
        If none of mbr eq or VOI is filled then we need only one between mono or multi
        """
        cleaned_data = self.cleaned_data
        pmonodn = cleaned_data.get("pmonodn")
        pmonopos = cleaned_data.get("pmonopos")
        pmonotime = cleaned_data.get("pmonotime")
        pmuldn = cleaned_data.get("pmuldn")
        pmulpos = cleaned_data.get("pmulpos")
        pmultime = cleaned_data.get("pmultime")
        mbreqdn = cleaned_data.get("mbreqdn")
        mbreqtime = cleaned_data.get("mbreqtime")
        vaitime = cleaned_data.get("vaitime")
        vaipos = cleaned_data.get("vaipos")
        simu = cleaned_data.get("simu")

        pmono_selected = False
        pmul_selected = False
        vai_selected = False
        mbreq_selected = False

        if mbreqdn and mbreqtime:
            mbreq_selected = True

        if pmonotime and pmonodn and pmonopos:
            pmono_selected = True

        if pmultime and pmuldn and pmulpos:
            pmul_selected = True

        if vaitime and vaipos:
            vai_selected = True

        # rule 1: mono ou multi non présent et mbrequipage ou vol aux instruments non plus
        if not mbreq_selected and not vai_selected and not simu and not (pmono_selected or pmul_selected):
            msg = "Vous devez renseigner au moins un vol monomoteur ou multimoteur."
            raise forms.ValidationError(msg)
        # rule 2
        if pmono_selected and pmul_selected:
            msg = "Vous ne pouvez valider un vol monomoteur et multimoteur en\
                    même temps."
            raise forms.ValidationError(msg)

        return cleaned_data

    def save(self, user, logbook, files, log=None):
        """
        Save log (update or create)
        """
        date_now = datetime.now()
        cleaned_data = self.cleaned_data
        mbreqdn = cleaned_data.get("mbreqdn")
        mbreqtime = cleaned_data.get("mbreqtime")
        pmonodn = cleaned_data.get("pmonodn")
        pmonopos = cleaned_data.get("pmonopos")
        pmonotime = cleaned_data.get("pmonotime")
        pmuldn = cleaned_data.get("pmuldn")
        pmulpos = cleaned_data.get("pmulpos")
        pmultime = cleaned_data.get("pmultime")
        vaidn = cleaned_data.get("vaidn")
        vaipos = cleaned_data.get("vaipos")
        vaitime = cleaned_data.get("vaitime")

        # mbr eq
        mbr_equipage_jour = 0
        mbr_equipage_nuit = 0
        if mbreqdn and mbreqdn == "d":
            mbr_equipage_jour = mbreqtime
        if mbreqdn and mbreqdn == "n":
            mbr_equipage_nuit = mbreqtime

        # mono
        mono_jdbl = 0
        mono_jcdb = 0
        mono_ndbl = 0
        mono_ncdb = 0
        # mono day double
        if pmonodn and pmonodn == "d" and pmonopos == "d":
            mono_jdbl = pmonotime
        # mono day c de bord
        if pmonodn and pmonodn == "d" and pmonopos == "c":
            mono_jcdb = pmonotime
        # mono night double
        if pmonodn and pmonodn == "n" and pmonopos == "d":
            mono_ndbl = pmonotime
        # mono night c de bord
        if pmonodn and pmonodn == "n" and pmonopos == "c":
            mono_ncdb = pmonotime

        # multi
        mul_jdbl = 0
        mul_jcdb = 0
        mul_jcplt = 0
        mul_ndbl = 0
        mul_ncdb = 0
        mul_ncplt = 0

        # multi day double
        if pmuldn and pmuldn == "d" and pmulpos == "d":
            mul_jdbl = pmultime
        # multi day c de bord
        if pmuldn and pmuldn == "d" and pmulpos == "c":
            mul_jcdb = pmultime
        # multi day co pilote
        if pmuldn and pmuldn == "d" and pmulpos == "co":
            mul_jcplt = pmultime
        # multi night double
        if pmuldn and pmuldn == "n" and pmulpos == "d":
            mul_ndbl = pmultime
        # multi night c de bord
        if pmuldn and pmuldn == "n" and pmulpos == "c":
            mul_ncdb = pmultime
        # multi night co pilote
        if pmuldn and pmuldn == "n" and pmulpos == "co":
            mul_ncplt = pmultime

        # VAI
        vai_dbl = 0
        vai_plt = 0

        if vaitime and vaipos == "d":
            vai_dbl = vaitime
        elif vaitime and vaipos == "c":
            vai_plt = vaitime

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
        ifr = cleaned_data["ifr"]
        if not ifr:
            ifr = 0
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
            nbrla = 0

        # staffob is a string with name separated by ';'
        staffob = ";".join(
            [
                cleaned_data["passengerA"],
                cleaned_data["passengerB"],
                cleaned_data["passengerC"],
            ]
        )

        if not log:
            log = DGACAvionLog()

        log.lbook = logbook

        log.cdate = cdate
        log.update = update

        log.date = date
        log.aeronef_type = cleaned_data["ltype"]
        log.aeronef_imma = cleaned_data["imma"]
        log.fctbrd = cleaned_data["fboard"]

        log.natvol = cleaned_data["nvol"]
        log.mbr_equipage_jour = mbr_equipage_jour
        log.mbr_equipage_nuit = mbr_equipage_nuit
        log.mono_jdbl = mono_jdbl
        log.mono_jcdb = mono_jcdb
        log.mono_ndbl = mono_ndbl
        log.mono_ncdb = mono_ncdb

        log.mul_jdbl = mul_jdbl
        log.mul_jcdb = mul_jcdb
        log.mul_jcplt = mul_jcplt
        log.mul_ndbl = mul_ndbl
        log.mul_ncdb = mul_ncdb
        log.mul_ncplt = mul_ncplt
        log.optional_filter = cleaned_data["optional_filter"]
        log.vai_dbl = vai_dbl
        log.vai_plt = vai_plt

        log.simu = cleaned_data["simu"]
        log.ifr = ifr
        log.obs = obs
        log.nbrla = nbrla
        log.nbrto = nbrto
        log.airpdep = cleaned_data["aerostart"]
        log.airpar = cleaned_data["aeroend"]
        log.staffob = staffob
        log.cmmts = coms

        return log
