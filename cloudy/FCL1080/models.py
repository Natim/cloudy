# System imports {{{

# }}}
# Django imports {{{
from django.db import models

from cloudy.FCL1080.fcl1080_pdfgen import gen_carnet_de_vol

# }}}
# Cloudy {{{
from cloudy.logbooks.models import LogBase, LogBookBase

# }}}


class FCL1080Log(LogBase):
    # Fields {{{
    departure_place = models.CharField(max_length=200, db_index=True)
    departure_time = models.IntegerField()
    arrival_place = models.CharField(max_length=200, db_index=True)
    arrival_time = models.IntegerField()

    aircraft_type = models.CharField(max_length=256, db_index=True)
    aircraft_imma = models.CharField(max_length=256, db_index=True)

    single_pilot_se = models.BooleanField(default=False)
    single_pilot_me = models.BooleanField(default=False)

    single_pilot_time = models.IntegerField()
    multi_pilot_time = models.IntegerField()
    total_time_flight = models.IntegerField()
    name_pic = models.CharField(max_length=30, db_index=True)
    take_off_day = models.PositiveIntegerField(default=0, null=True, blank=True)
    take_off_night = models.PositiveIntegerField(default=0, null=True, blank=True)
    landing_day = models.PositiveIntegerField(default=0, null=True, blank=True)
    landing_night = models.PositiveIntegerField(default=0, null=True, blank=True)

    op_time_night = models.IntegerField()
    op_time_ifr = models.IntegerField()

    pilot_time_in_cmd = models.IntegerField()
    pilot_timpe_cop = models.IntegerField()
    pilot_time_dual = models.IntegerField()
    pilot_time_inst = models.IntegerField()

    synthetic_date = models.DateTimeField(blank=True, null=True, db_index=True)
    synthetic_type = models.CharField(max_length=30, db_index=True)
    synthetic_time = models.IntegerField(default=0)

    obs = models.CharField(max_length=400)
    # Commentaires
    cmmts = models.CharField(max_length=400)

    # Staff on board
    staffob = models.CharField(max_length=400)

    # }}}
    # Inherited methods {{{
    def __unicode__(self):
        return "%s" % self.aircraft_imma

    # }}}

    def json_rules(self):
        return super().json_rules() + [
            ("departure_place", "string"),
            ("departure_time", "string"),
            ("arrival_place", "string"),
            ("arrival_time", "string"),
            ("aircraft_type", "string"),
            ("aircraft_imma", "string"),
            ("single_pilot_se", "integer"),
            ("single_pilot_me", "integer"),
            ("multi_pilot_time", "integer"),
            ("total_time_flight", "integer"),
            ("name_pic", "string"),
            ("take_off_day", "integer"),
            ("take_off_night", "integer"),
            ("landing_day", "integer"),
            ("landing_night", "integer"),
            ("op_time_night", "integer"),
            ("op_time_ifr", "integer"),
            ("pilot_time_in_cmd", "integer"),
            ("pilot_timpe_cop", "integer"),
            ("pilot_time_dual", "integer"),
            ("pilot_time_inst", "integer"),
            ("synthetic_date", "date"),
            ("synthetic_type", "string"),
            ("synthetic_time", "integer"),
            ("obs", "string"),
            ("cmmts", "string"),
            ("staffob", "list"),
        ]


class FCL1080LogBook(LogBookBase):
    # Associated models {{{
    @classmethod
    def _log_model(cls):
        return FCL1080Log

    # }}}

    def pdf_gen_method(self):
        return gen_carnet_de_vol

    # Inherited {{{
    @classmethod
    def rows_per_page(cls):
        return 12

    # }}}
    # Rules sets {{{
    def totals_rules(self):
        """
        Returns the rules to compute totals.
        """

        rules = {
            "total_single_pilot_time": ["single_pilot_time"],
            "total_multi_pilot_time": ["multi_pilot_time"],
            "total_total_time_flight": ["total_time_flight"],
            "total_landing": ["landing_day", "landing_night"],
            "total_landing_night": ["landing_night"],
            "total_landing_day": ["landing_day"],
            "total_take_off": ["take_off_night", "take_off_day"],
            "total_take_off_night": ["take_off_night"],
            "total_take_off_day": ["take_off_day"],
            "total_op_time": ["op_time_night", "op_time_ifr"],
            "total_op_time_night": ["op_time_night"],
            "total_op_time_ifr": ["op_time_ifr"],
            "total_pilot_time": [
                "pilot_time_in_cmd",
                "pilot_timpe_cop",
                "pilot_time_dual",
                "pilot_time_inst",
            ],
            "total_pilot_time_in_cmd": ["pilot_time_in_cmd"],
            "total_pilot_timpe_cop": ["pilot_timpe_cop"],
            "total_pilot_time_dual": ["pilot_time_dual"],
            "total_pilot_time_inst": ["pilot_time_inst"],
            "total_synthetic_time": ["synthetic_time"],
        }
        return rules

    def totals_page_totals(self):
        return [
            "total_single_pilot_time",
            "total_multi_pilot_time",
            "total_total_time_flight",
            "total_take_off",
            "total_take_off_day",
            "total_take_off_night",
            "total_landing",
            "total_landing_day",
            "total_landing_night",
            "total_op_time",
            "total_op_time_night",
            "total_op_time_ifr",
            "total_pilot_time_in_cmd",
            "total_pilot_timpe_cop",
            "total_pilot_time_dual",
            "total_pilot_time_inst",
            "total_synthetic_time",
            "total_pilot_time",
        ]

    def home_page_totals(self):
        return self.totals_page_totals()

    def csv_rules(self):
        return [
            ("date", "date", "", False, "Date"),
            ("departure_place", "string", "", False, "Departure place"),
            ("departure_time", "time", "", False, "Departure time"),
            ("arrival_place", "string", "", False, "Arrival place"),
            ("arrival_time", "time", "", False, "Arrival time"),
            ("aircraft_type", "string", "", False, "Aircraft type"),
            ("aircraft_imma", "string", "", False, "Aircraft Immatriculation"),
            ("single_pilot_se", "bool", "", False, "Single pilot time (0 -> False, 1-> True)"),
            ("single_pilot_me", "bool", "", False, "Multi pilot time (0 -> False, 1-> True)"),
            ("single_pilot_time", "time", 0, True, "Single pilot time"),
            ("multi_pilot_time", "time", 0, True, "Multi pilot time"),
            ("total_time_flight", "time", 0, False, "Total time of flight"),
            ("name_pic", "string", "", False, "Name PIC"),
            ("take_off_day", "int", 0, True, "Number of takeoffs day"),
            ("take_off_night", "int", 0, True, "Number of takeoffs night"),
            ("landing_day", "int", 0, True, "Number of landings day"),
            ("landing_night", "int", 0, True, "Number of landings night"),
            ("op_time_night", "time", 0, True, "Operational condition time: Night"),
            ("op_time_ifr", "time", 0, True, "Operational condition time: IFR"),
            ("pilot_time_in_cmd", "time", 0, True, "Pilote function time: pilot in command"),
            ("pilot_timpe_cop", "time", 0, True, "Pilote function time: co-pilot"),
            ("pilot_time_dual", "time", 0, True, "Pilote function time: dual"),
            ("pilot_time_inst", "time", 0, True, "Pilote function time: instructor"),
            ("synthetic_date", "date", None, True, "Synthetic training device date"),
            ("synthetic_type", "string", "", True, "Synthetic training type"),
            ("synthetic_time", "time", 0, True, "Synthetic training time"),
            ("obs", "string", "", True, "Observations ..."),
            ("staffob", "string", "", True, "Personnes a bord"),
            ("cmmts", "string", "", True, "Commentaires"),
        ]

    # }}}
    # Associated models {{{
    @classmethod
    def _log_model(cls):
        return FCL1080Log

    @classmethod
    def _report_form_model(cls):
        from cloudy.FCL1080.forms import FCL1080ReportForm

        return FCL1080ReportForm

    @classmethod
    def _log_form_model(cls):
        from cloudy.FCL1080.forms import FCL1080LogForm

        return FCL1080LogForm

    # }}}

    @property
    def can_fly(self):
        return True

    def attach_pdf_to_http_response(self, http_response, title, show_cuts=True):
        """
        Attaches the logbook pdf as the http response object (if passed)
        """
        logs = list(self.logs_qs())
        gen_carnet_de_vol(http_response, title, show_cuts, logs, self.reports)
