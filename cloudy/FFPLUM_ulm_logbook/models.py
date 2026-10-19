# Django imports {{{
from django.db import models

from cloudy.FFPLUM_ulm_logbook.ffplum_ulm_pdfgen import gen_carnet_de_vol

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
    "Heure de vol Cdt de bord (min)",
    "Heures de vol instructeur (min)",
    "Observations / Nature du vol",
    "Nombre de decollages",
    "Nombre d'atterrissages",
    "Aerodrome départ",
    "Aerodrome arrivée",
    "Personnes à bord",
    "Commentaires",
]

DOUBLE_CDB = (
    ("c", "Cdt de bord"),
    ("d", "Double commande"),
)


# }}}


class FFPLUMUlmLog(LogBase):
    # Fields {{{
    # 'Type'
    ulm_type = models.CharField(max_length=30, blank=False, db_index=True)
    ulm_imma = models.CharField(max_length=50, blank=False, db_index=True)

    # 'Heures De Vol - Double'
    flytime_dbl = models.IntegerField()
    # 'Heures De Vol - Cdt de Bord'
    flytime_cdb = models.IntegerField()

    # Observations et visa de ...
    obs = models.CharField(max_length=200)
    # Commentaires
    cmmts = models.CharField(max_length=4000)

    # Other non DGAC fields
    # Number of take offs
    nbrto = models.IntegerField()
    # Number of landings
    nbrla = models.IntegerField()
    # Staff on board
    staffob = models.CharField(max_length=200)
    # }}}

    def __unicode__(self):
        return f"{self.ulm_type} {self.date}"

    def json_rules(self):
        return super().json_rules() + [
            ("ulm_type", "string"),
            ("ulm_imma", "string"),
            ("flytime_dbl", "integer"),
            ("flytime_cdb", "integer"),
            ("obs", "string"),
            ("cmmts", "string"),
            ("nbrto", "integer"),
            ("nbrla", "integer"),
            ("airpdep", "string"),
            ("airpar", "string"),
            ("staffob", "list"),
        ]


class FFPLUMUlmLogBook(LogBookBase):
    # Inherited {{{
    @classmethod
    def rows_per_page(cls):
        return 9

    def __unicode__(self):
        return "FPPLUM "

    # }}}
    # Rules sets {{{
    def totals_rules(self):
        """
        Returns the rules to compute totals.
        """
        rules = {
            "total_double": ["flytime_dbl"],
            "total_captain": ["flytime_cdb"],
            "total_flight_hours": ["flytime_dbl", "flytime_cdb"],
            "total_takeoff": ["nbrto"],
            "total_landing": ["nbrla"],
        }
        return rules

    def totals_page_totals(self):
        return [
            "total_double",
            "total_captain",
            "total_flight_hours",
            "total_takeoff",
            "total_landing",
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
            ("ulm_type", "string", "", False, "Type Ulm"),
            ("ulm_imma", "string", "", False, "Immatriculation"),
            ("flytime_dbl", "time", 0, True, "Heures de vol Double commande"),
            ("flytime_cdb", "time", 0, True, "Heures de vol Cdt de bord"),
            ("obs", "string", "", True, "Observations ..."),
            ("nbrto", "int", 0, True, "Nombre takeoff"),
            ("nbrla", "int", 0, True, "Nombre landing"),
            ("airpdep", "string", "", True, "Aerodrome depart"),
            ("airpar", "string", "", True, "Aerodrome arrivee"),
            ("staffob", "string", "", True, "Personnes a bord"),
            ("cmmts", "string", "", True, "Commentaires"),
        ]

    # }}}
    # Associated models {{{
    @classmethod
    def _log_model(cls):
        return FFPLUMUlmLog

    @classmethod
    def _log_form_model(cls):
        from cloudy.FFPLUM_ulm_logbook.forms import FFPLUMUlmLogForm

        return FFPLUMUlmLogForm

    @classmethod
    def _report_form_model(cls):
        from cloudy.FFPLUM_ulm_logbook.forms import FFPLUMUlmReportForm

        return FFPLUMUlmReportForm

    # }}}

    def attach_pdf_to_http_response(self, http_response, title, show_cuts=True):
        """
        Attaches the logbook pdf as the http response object (if passed)
        """
        logs = list(self.logs_qs())
        gen_carnet_de_vol(http_response, title, show_cuts, logs, self.reports)
