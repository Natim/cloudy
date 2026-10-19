# System imports {{{

# }}}
# Django imports {{{
from django.db import models

from cloudy.DGAC_planeur_logbook.dgac_planeur_pdfgen import gen_carnet_de_vol

# }}}
# Cloudy {{{
from cloudy.logbooks.models import LogBase, LogBookBase

# }}}


# Data {{{
CSV_ROWS_HEADER = [
    "Année",
    "Date",
    "Type aeronef",
    "Immatriculation",
    "Function a bord",
    "Nature du vol ([L]ocal [C]ampagne [V]oltige)",
    "Méthode de lancement ([R]emorqué [T]reuil [A]utonome)",
    "Heures de vol double (min)",
    "Heure de vol Cdt de bord (min)",
    "Heures de vol instructeur (min)",
    "Observations et visa de l'autorite habilitee ou de l'instructeur",
    "Aerodrome départ",
    "Aerodrome arrivée",
    "Personnes à bord",
    "Commentaires",
]

FUNCTION_ON_BOARD = (
    ("EP", "Elève Pilote"),
    ("Cdb", "Commandant de bord"),
    ("Pilote", "Pilote"),
    ("Co-pilote", "Co-pilote"),
    ("Inst", "Instructeur"),
    ("Exam", "Examinateur"),
    ("EPFI", "EPFI"),
)

NATVOL = (
    ("L", "Local"),
    ("C", "Campagne"),
    ("V", "Voltige"),
    ("CV", "Convoyage"),
    ("CO", "Compétition"),
)

LAUNCH_MODE = (
    ("R", "Remorqué"),
    ("T", "Treuil"),
    ("A", "Autonome"),
)

DOUBLE_CDB_INS = (
    ("c", "Cdt de bord"),
    ("d", "Double commande"),
    ("i", "Instructeur"),
)

# }}}


class DGACPlaneurLog(LogBase):
    # Fields {{{
    glider_type = models.CharField(max_length=30, blank=False, db_index=True)
    glider_imma = models.CharField(max_length=30, blank=False, db_index=True)

    flytime_dbl = models.IntegerField()
    flytime_cdb = models.IntegerField()
    flytime_ins = models.IntegerField()

    # 'Function à bord'
    fctbrd = models.CharField(max_length=10, db_index=True)
    # 'Nature du vol'
    natvol = models.CharField(max_length=10, db_index=True)
    # 'Mode de Lancement'
    lmode = models.CharField(max_length=10, db_index=True)

    # Observations et visa de ...
    obs = models.CharField(max_length=200)
    # Commentaires
    cmmts = models.CharField(max_length=4000)

    # Other non DGAC fields
    # Number of take offs
    nbrto = models.IntegerField(default=0, null=True, blank=True)
    # Number of landings
    nbrla = models.IntegerField(default=0, null=True, blank=True)

    # Staff on board
    staffob = models.CharField(max_length=200)
    # }}}
    # Fucking hack {{{
    # Add those constants so that we can access them from
    # our templates in a generic fashion when building
    # dynamic js form.
    FUNCTION_ON_BOARD = FUNCTION_ON_BOARD
    NATVOL = NATVOL
    LAUNCH_MODE = LAUNCH_MODE
    # }}}
    # Inherited methods {{{

    def __unicode__(self):
        return "%s" % self.glider_imma

    # }}}

    def json_rules(self):
        return super().json_rules() + [
            ("glider_type", "string"),
            ("glider_imma", "string"),
            ("flytime_dbl", "integer"),
            ("flytime_cdb", "integer"),
            ("flytime_ins", "integer"),
            ("fctbrd", "integer"),
            ("natvol", "integer"),
            ("lmode", "integer"),
            ("obs", "string"),
            ("cmmts", "string"),
            ("nbrto", "integer"),
            ("nbrla", "integer"),
            ("airpdep", "string"),
            ("airpar", "string"),
            ("staffob", "list"),
        ]


class DGACPlaneurLogBook(LogBookBase):
    def pdf_gen_method(self):
        return gen_carnet_de_vol

    # Inherited {{{
    @classmethod
    def rows_per_page(cls):
        return 14

    # }}}
    # Rules sets {{{
    def totals_rules(self):
        """
        Returns the rules to compute totals.
        """

        rules = {
            "total_double": ["flytime_dbl"],
            "total_captain": ["flytime_cdb"],
            "total_instruct": ["flytime_ins"],
            "total_flight_hours": ["flytime_dbl", "flytime_cdb", "flytime_ins"],
        }
        return rules

    def totals_page_totals(self):
        return [
            "total_double",
            "total_captain",
            "total_instruct",
            "total_flight_hours",
        ]

    def home_page_totals(self):
        return self.totals_page_totals()

    def csv_rules(self):
        """
        CSV import rules for safety check.
        A rule is a tuple with the format:
        (checking type, row id, name, rule name, can be empty)
        """
        return [
            ("date", "date", "", False, "Date"),
            ("glider_type", "string", "", False, "Type Planneur"),
            ("glider_imma", "string", "", False, "Immatriculation"),
            ("fctbrd", "string", "", False, "Function a bord"),
            ("natvol", "string", "", False, "Nature du vol"),
            ("lmode", "string", "", False, "Mode de lancement"),
            ("flytime_dbl", "time", 0, True, "Heures de vol Double commande"),
            ("flytime_cdb", "time", 0, True, "Heures de vol Cdt de bord"),
            ("flytime_ins", "time", 0, True, "Heures de vol Instructeur"),
            ("obs", "string", "", True, "Observations ..."),
            ("airpdep", "string", "", True, "Aerodrome depart"),
            ("airpar", "string", "", True, "Aerodrome arrivee"),
            ("staffob", "string", "", True, "Personnes a bord"),
            ("cmmts", "string", "", True, "Commentaires"),
        ]

    # }}}
    # Associated models {{{
    @classmethod
    def _log_model(cls):
        return DGACPlaneurLog

    @classmethod
    def _report_form_model(cls):
        from forms import DGACPlaneurReportForm

        return DGACPlaneurReportForm

    @classmethod
    def _log_form_model(cls):
        from cloudy.DGAC_planeur_logbook.forms import DGACPlaneurLogForm

        return DGACPlaneurLogForm

    # }}}

    def attach_pdf_to_http_response(self, http_response, title, show_cuts=True):
        """
        Attaches the logbook pdf as the http response object (if passed)
        """
        logs = list(self.logs_qs())
        gen_carnet_de_vol(http_response, title, show_cuts, logs, self.reports)
