# Django imports {{{
from django.db import models

from cloudy.DGAC_avion_logbook.dgac_avion_pdfgen import gen_carnet_de_vol

# }}}
# Cloudy {{{
from cloudy.logbooks.models import LogBase, LogBookBase


class DGACAvionLog(LogBase):
    # Fields {{{
    #  'Aeronef'
    aeronef_type = models.CharField(max_length=256, db_index=True)
    aeronef_imma = models.CharField(max_length=256, db_index=True)
    # 'Function à bord'
    fctbrd = models.CharField(max_length=40, db_index=True)
    # 'Nature du vol'
    natvol = models.CharField(max_length=100)
    # 'Membre d'equipage'
    mbr_equipage_jour = models.IntegerField()
    mbr_equipage_nuit = models.IntegerField()
    # 'Pilote monomoteur : jour / nuit : Double / cdt de bord ...
    mono_jdbl = models.IntegerField()
    mono_jcdb = models.IntegerField()
    mono_ndbl = models.IntegerField()
    mono_ncdb = models.IntegerField()
    # 'Pilote multimoteurs '
    mul_jdbl = models.IntegerField()
    mul_jcdb = models.IntegerField()
    mul_jcplt = models.IntegerField()
    mul_ndbl = models.IntegerField()
    mul_ncdb = models.IntegerField()
    mul_ncplt = models.IntegerField()
    # 'Vols aux instruments'
    vai_dbl = models.IntegerField()
    vai_plt = models.IntegerField()
    # Simulation
    simu = models.IntegerField()
    # Arrivées I.F.R
    ifr = models.IntegerField()
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
    # Inherited methods {{{
    def __unicode__(self):
        return "%s" % self.aeronef_imma

    # }}}

    def json_rules(self):
        return super().json_rules() + [
            ("aeronef_type", "string"),
            ("aeronef_imma", "string"),
            ("fctbrd", "string"),
            ("natvol", "string"),
            ("mbr_equipage_jour", "integer"),
            ("mbr_equipage_nuit", "integer"),
            ("mono_jdbl", "integer"),
            ("mono_jcdb", "integer"),
            ("mono_ndbl", "integer"),
            ("mono_ncdb", "integer"),
            ("mul_jdbl", "integer"),
            ("mul_jcdb", "integer"),
            ("mul_jcplt", "integer"),
            ("mul_ndbl", "integer"),
            ("mul_ncdb", "integer"),
            ("mul_ncplt", "integer"),
            ("vai_dbl", "integer"),
            ("vai_plt", "integer"),
            ("simu", "integer"),
            ("ifr", "integer"),
            ("obs", "string"),
            ("cmmts", "string"),
            ("nbrto", "integer"),
            ("nbrla", "integer"),
            ("airpdep", "string"),
            ("airpar", "string"),
            ("staffob", "list"),
        ]


class DGACAvionLogBook(LogBookBase):
    def pdf_gen_method(self):
        return gen_carnet_de_vol

    # Associated models {{{
    @classmethod
    def _log_model(cls):
        return DGACAvionLog

    @classmethod
    def _report_form_model(cls):
        from .forms import DGACAvionReportForm

        return DGACAvionReportForm

    @classmethod
    def _log_form_model(cls):
        from .forms import DGACAvionLogForm

        return DGACAvionLogForm

    # }}}
    # Rules sets {{{

    def csv_rules(self):
        return [
            ("date", "date", "", False, "Date"),
            ("aeronef_type", "string", "", False, "Type Aeronef"),
            ("aeronef_imma", "string", "", False, "Immatriculation"),
            ("fctbrd", "string", "", False, "Function a bord"),
            ("natvol", "string", "", False, "Nature du vol"),
            ("mbr_equipage_jour", "time", 0, True, "Membre d'equipage Jour"),
            ("mbr_equipage_nuit", "time", 0, True, "Membre d'equipage Nuit"),
            ("mono_jdbl", "time", 0, True, "Pilote monomoteur Jour Double"),
            ("mono_jcdb", "time", 0, True, "Pilote monomoteur Jour Cdt de bord"),
            ("mono_ndbl", "time", 0, True, "Pilote monomoteur Nuit Double"),
            ("mono_ncdb", "time", 0, True, "Pilote monomoteur Nuit Cdt de bord"),
            ("mul_jdbl", "time", 0, True, "Pilote multimoteurs Jour Double"),
            ("mul_jcdb", "time", 0, True, "Pilote multimoteurs Jour Cdt de bord"),
            ("mul_jcplt", "time", 0, True, "Pilote multimoteurs Jour co-pilote"),
            ("mul_ndbl", "time", 0, True, "Pilote multimoteurs Nuit Double"),
            ("mul_ncdb", "time", 0, True, "Pilote multimoteurs Nuit Cdt de bord"),
            ("mul_ncplt", "time", 0, True, "Pilote multimoteurs Nuit co-pilote"),
            ("vai_dbl", "time", 0, True, "Vols aux instruments Double"),
            ("vai_plt", "time", 0, True, "Vols aux instruments Pilote"),
            ("simu", "time", 0, True, "Simulation"),
            ("ifr", "int", 0, True, "Arrivees IFR"),
            ("obs", "string", "", True, "Observations ..."),
            ("nbrla", "int", 0, True, "Nombre landing"),
            ("nbrto", "int", 0, True, "Nombre takeoff"),
            ("airpdep", "string", "", True, "Aerodrome depart"),
            ("airpar", "string", "", True, "Aerodrome arrivee"),
            ("staffob", "string", "", True, "Personnes a bord"),
            ("cmmts", "string", "", True, "Commentaires"),
        ]

    def totals_rules(self):
        """Returns the rules to compute totals."""
        return {
            "total_mbr_equipage_jour": ["mbr_equipage_jour"],
            "total_mbr_equipage_nuit": ["mbr_equipage_nuit"],
            "total_mono_day_double": ["mono_jdbl"],
            "total_mono_day_captain": ["mono_jcdb"],
            "total_mono_night_double": ["mono_ndbl"],
            "total_mono_night_captain": ["mono_ncdb"],
            "total_multi_day_double": ["mul_jdbl"],
            "total_multi_day_captain": ["mul_jcdb"],
            "total_multi_day_copilot": ["mul_jcplt"],
            "total_multi_night_double": ["mul_ndbl"],
            "total_multi_night_captain": ["mul_ncdb"],
            "total_multi_night_copilot": ["mul_ncplt"],
            "total_instruments_double": ["vai_dbl"],
            "total_instruments_pilot": ["vai_plt"],
            "total_instruments": ["vai_dbl", "vai_plt"],
            "total_takeoff": ["nbrto"],
            "total_landing": ["nbrla"],
            "total_simu": ["simu"],
            "total_ifr": ["ifr"],
            "total_multi_night": ["mul_ndbl", "mul_ncdb", "mul_ncplt"],
            "total_multi_day": ["mul_jdbl", "mul_jcdb", "mul_jcplt"],
            "total_multi_double": ["mul_jdbl", "mul_ndbl"],
            "total_multi_captain": ["mul_jcdb", "mul_ncdb"],
            "total_multi_copilot": ["mul_jcplt", "mul_ncplt"],
            "total_multi": [
                "mul_ndbl",
                "mul_ncdb",
                "mul_ncplt",
                "mul_jdbl",
                "mul_jcdb",
                "mul_jcplt",
            ],
            "total_mono_day": ["mono_jdbl", "mono_jcdb"],
            "total_mono_night": ["mono_ndbl", "mono_ncdb"],
            "total_mono_double": ["mono_ndbl", "mono_jdbl"],
            "total_mono_captain": ["mono_jcdb", "mono_ncdb"],
            "total_mono": ["mono_jdbl", "mono_jcdb", "mono_ndbl", "mono_ncdb"],
            "total_mbr_equipage": ["mbr_equipage_jour", "mbr_equipage_nuit"],
            "total_captain": ["mono_jcdb", "mono_ncdb", "mul_jcdb", "mul_ncdb"],
            "total_double": ["mono_ndbl", "mono_jdbl", "mul_jdbl", "mul_ndbl"],
            "total_day": ["mono_jdbl", "mono_jcdb", "mul_jdbl", "mul_jcdb", "mul_jcplt"],
            "total_night": ["mono_ndbl", "mono_ncdb", "mul_ndbl", "mul_ncdb", "mul_ncplt"],
            "total_pilot_flight": [
                "mono_jdbl",
                "mono_jcdb",
                "mono_ndbl",
                "mul_ncplt",
                "mono_ncdb",
                "mul_jdbl",
                "mul_jcdb",
                "mul_jcplt",
                "mul_ndbl",
                "mul_ncdb",
            ],
        }

    def home_page_totals(self):
        return [
            "total_mbr_equipage_jour",
            "total_mbr_equipage_nuit",
            "total_mono_day_double",
            "total_mono_day_captain",
            "total_mono_night_double",
            "total_mono_night_captain",
            "total_multi_day_double",
            "total_multi_day_captain",
            "total_multi_day_copilot",
            "total_multi_night_double",
            "total_multi_night_captain",
            "total_multi_night_copilot",
            "total_instruments_double",
            "total_instruments_pilot",
            "total_simu",
            "total_ifr",
        ]

    def totals_page_totals(self):
        return [
            "total_pilot_flight",
            "total_day",
            "total_night",
            "total_mbr_equipage",
            "total_mbr_equipage_jour",
            "total_mbr_equipage_nuit",
            "total_instruments",
            "total_instruments_double",
            "total_instruments_pilot",
            "total_mono",
            "total_mono_day",
            "total_mono_night",
            "total_mono_captain",
            "total_mono_double",
            "total_mono_day_double",
            "total_mono_day_captain",
            "total_mono_night_captain",
            "total_mono_night_double",
            "total_multi",
            "total_multi_day",
            "total_multi_night",
            "total_multi_day_double",
            "total_multi_day_captain",
            "total_multi_day_copilot",
            "total_multi_night_double",
            "total_multi_night_captain",
            "total_multi_night_copilot",
            "total_multi_day_captain",
            "total_multi_day_double",
            "total_multi_day_copilot",
            "total_multi_night_captain",
            "total_multi_night_copilot",
            "total_multi_night_copilot",
            "total_takeoff",
            "total_landing",
            "total_simu",
        ]

    # }}}
