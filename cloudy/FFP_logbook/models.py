# System imports {{{

# }}}
# Django imports {{{
from django.db import models

from cloudy.FFP_logbook.ffp_pdfgen import gen_carnet_de_vol

# }}}
# Cloudy {{{
from cloudy.logbooks.models import LogBase, LogBookBase

# }}}


class FFPLog(LogBase):
    # Fields {{{
    jump_count = models.IntegerField(default=1)
    falling_time = models.IntegerField(default=0)

    place = models.CharField(max_length=200)
    aircraft = models.CharField(max_length=30, db_index=True)
    # 'Sauts '
    altitude = models.IntegerField()
    altitude_open = models.IntegerField(default=0, null=True, blank=True)

    canopy = models.CharField(max_length=30, db_index=True)
    bag = models.CharField(max_length=30, db_index=True)

    perf_exercise = models.CharField(max_length=255, db_column="perf_exercice")
    freefall_training = models.CharField(max_length=255)
    canopy_piloting = models.CharField(max_length=255)
    # Commentaires
    cmmts = models.CharField(max_length=400)

    # Inherited methods {{{
    def __unicode__(self):
        return "%s" % self.aircraft

    # }}}

    def json_rules(self):
        return super().json_rules() + [
            ("place", "string"),
            ("aircraft", "string"),
            ("altitude", "integer"),
            ("altitude_open", "integer"),
            ("canopy", "string"),
            ("bag", "string"),
            ("perf_exercise", "string"),
            ("freefall_training", "string"),
            ("canopy_piloting", "string"),
            ("cmmts", "string"),
            ("falling_time", "integer"),
        ]


class FFPLogBook(LogBookBase):
    # Associated models {{{
    @classmethod
    def _log_model(cls):
        return FFPLog

    # }}}

    def pdf_gen_method(self):
        return gen_carnet_de_vol

    # Inherited {{{
    @classmethod
    def rows_per_page(cls):
        return 6

    # }}}
    # Rules sets {{{
    def totals_rules(self):
        """
        Returns the rules to compute totals.
        """

        rules = {
            "total_jumps": ["jump_count"],
            "total_altitude": ["altitude"],
            "total_altitude_open": ["altitude_open"],
            "total_falling": ["falling_time"],
        }
        return rules

    def totals_page_totals(self):
        return ["total_jumps", "total_altitude", "total_altitude_open", "total_falling"]

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
            ("place", "string", "", False, "Lieu (Place)"),
            ("aircraft", "string", "", False, "Aéronef (aircraft)"),
            ("altitude", "int", 0, False, "Hauteur (altitude)"),
            ("canopy", "string", "", False, "Voilure principale (Main Canopy)"),
            ("perf_exercise", "string", "", False, "Programme du saut (Performed exercise)"),
            ("freefall_training", "string", "", False, "Exercise en chute (Freefall training)"),
            ("canopy_piloting", "string", "", False, "Exercise sous voile (Canopy piloting)"),
            ("cmmts", "string", "", True, "Commentaires"),
            ("altitude_open", "int", 0, True, "Hauteur d'ouverture"),
            ("falling_time", "time", 0, True, "Temps de chute"),
        ]

    # }}}
    # Associated models {{{
    @classmethod
    def _log_model(cls):
        return FFPLog

    @classmethod
    def _report_form_model(cls):
        from cloudy.FFP_logbook.forms import FFPReportForm

        return FFPReportForm

    @classmethod
    def _log_form_model(cls):
        from cloudy.FFP_logbook.forms import FFPLogForm

        return FFPLogForm

    # }}}

    @property
    def can_fly(self):
        return False

    def attach_pdf_to_http_response(self, http_response, title, show_cuts=True, include_images=False):
        """
        Attaches the logbook pdf as the http response object (if passed)
        """
        logs = list(self.logs_qs())
        gen_carnet_de_vol(http_response, title, show_cuts, logs, self.reports)
