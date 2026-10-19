import re
from datetime import datetime

import redis
from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from cloudy.accounts.models import UserProfile
from cloudy.core.utils import contains_html, patch_settings
from cloudy.DGAC_avion_logbook.models import DGACAvionLog
from cloudy.logbooks.forms import DeleteLbookForm
from cloudy.logbooks.models import LogBase, LogBookBase


class LogBookTestCase(TestCase):
    fixtures = ["testing_data.json"]

    def setUp(self):
        self.c = Client()
        self.c.login(email="pilot@example.com", password="azeaze")

    def teadDown(self):
        r = redis.Redis(host=settings.REDIS_SERVER, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        r.flushall()

    def _create_logbook(self):
        """Helper to create a fresh new logbook."""
        data = {"plane_dgac": 1}
        resp = self.c.post(reverse("logbooks:addlogbook"), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(LogBookBase.objects.filter(deleted=False)), 1)
        self.assertContains(resp, "DGAC Avion", 1)
        return LogBookBase.objects.all()[0]

    def test_reports_logs_split_middle_day(self):
        logbook = self._create_logbook()

        # 15, to it fills one page (14 logs) plus one.
        for i in range(15):
            data = {
                "ltype": ["T1"],
                "pmultime_0": [""],
                "pmultime_1": [""],
                "pmonotime_0": [""],
                "pmonotime_1": [""],
                "mbreqtime_0": ["1"],
                "mbreqtime_1": ["0"],
                "fboard": ["EP"],
                "aerostart": [""],
                "imma": ["M1"],
                "media": [""],
                "pmonopos": ["d"],
                "nvol": ["N1"],
                "coms": [""],
                "aeroend": [""],
                "vaitime_1": [""],
                "vaitime_0": [""],
                "passengerB": [""],
                "passengerC": [""],
                "landingcount": [""],
                "passengerA": [""],
                "date": ["04/07/2011"],
                "takeoffcount": [""],
                "mbreqdn": ["n"],
                "ifr": [""],
                "log_id": [""],
                "simu_0": [""],
                "pmonodn": ["n"],
                "simu_1": [""],
                "obs": [""],
            }
            resp = self.c.post(reverse("logbooks:add_log", args=[logbook.pk]), data, follow=True)
            self.assertEqual(resp.status_code, 200)

        resp = self.c.get(reverse("logbooks:home"), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(contains_html(resp.content, "td", "reports-info", text=re.compile(r"14:00")))

    def test_update_log_order(self):
        """Test log date order after edit."""

        logbook = self._create_logbook()

        # Add three logs
        # Log 1
        data = {
            "ltype": ["T1"],
            "pmultime_0": [""],
            "pmultime_1": [""],
            "pmonotime_0": ["0"],
            "pmonotime_1": ["20"],
            "mbreqtime_0": ["5"],
            "mbreqtime_1": ["10"],
            "fboard": ["EP"],
            "aerostart": [""],
            "imma": ["M1"],
            "media": [""],
            "pmonopos": ["d"],
            "nvol": ["N1"],
            "coms": ["Tapez ici vos commentaires"],
            "aeroend": [""],
            "vaitime_1": [""],
            "vaitime_0": [""],
            "passengerB": [""],
            "passengerC": [""],
            "landingcount": [""],
            "passengerA": [""],
            "date": ["04/07/2011"],
            "takeoffcount": [""],
            "mbreqdn": ["n"],
            "ifr": [""],
            "log_id": [""],
            "simu_0": [""],
            "pmonodn": ["n"],
            "simu_1": [""],
            "obs": ["Tapez ici les observations"],
        }

        resp = self.c.post(reverse("logbooks:add_log", args=[logbook.pk]), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(LogBase.objects.all()), 1)
        log1 = LogBase.objects.all()[0]
        self.assertContains(resp, "<pre>T1</pre>", 1)

        # Log 2
        data = {
            "ltype": ["T2"],
            "pmultime_0": [""],
            "pmultime_1": [""],
            "pmonotime_0": ["0"],
            "pmonotime_1": ["20"],
            "mbreqtime_0": ["5"],
            "mbreqtime_1": ["10"],
            "fboard": ["EP"],
            "aerostart": [""],
            "imma": ["M2"],
            "media": [""],
            "pmonopos": ["d"],
            "nvol": ["N2"],
            "coms": ["Tapez ici vos commentaires"],
            "aeroend": [""],
            "vaitime_1": [""],
            "vaitime_0": [""],
            "passengerB": [""],
            "passengerC": [""],
            "landingcount": [""],
            "passengerA": [""],
            "date": ["04/07/2011"],
            "takeoffcount": [""],
            "mbreqdn": ["n"],
            "ifr": [""],
            "log_id": [""],
            "simu_0": [""],
            "pmonodn": ["n"],
            "simu_1": [""],
            "obs": ["Tapez ici les observations"],
        }

        resp = self.c.post(reverse("logbooks:add_log", args=[logbook.pk]), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(LogBase.objects.all()), 2)
        self.assertContains(resp, "<pre>T2</pre>", 1)

        # Log 3
        data = {
            "ltype": ["T3"],
            "pmultime_0": [""],
            "pmultime_1": [""],
            "pmonotime_0": ["0"],
            "pmonotime_1": ["20"],
            "mbreqtime_0": ["5"],
            "mbreqtime_1": ["10"],
            "fboard": ["EP"],
            "aerostart": [""],
            "imma": ["M3"],
            "media": [""],
            "pmonopos": ["d"],
            "nvol": ["N3"],
            "coms": ["Tapez ici vos commentaires"],
            "aeroend": [""],
            "vaitime_1": [""],
            "vaitime_0": [""],
            "passengerB": [""],
            "passengerC": [""],
            "landingcount": [""],
            "passengerA": [""],
            "date": ["04/07/2011"],
            "takeoffcount": [""],
            "mbreqdn": ["n"],
            "ifr": [""],
            "log_id": [""],
            "simu_0": [""],
            "pmonodn": ["n"],
            "simu_1": [""],
            "obs": ["Tapez ici les observations"],
        }

        resp = self.c.post(reverse("logbooks:add_log", args=[logbook.pk]), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(LogBase.objects.all()), 3)
        self.assertContains(resp, "<pre>T3</pre>", 1)

        # Edit First log with form edit should not change its date !
        log1_date = log1.date
        log1_cdate = log1.cdate

        data = {
            "ltype": ["T1-edit"],
            "pmultime_0": [""],
            "pmultime_1": [""],
            "pmonotime_0": ["0"],
            "pmonotime_1": ["20"],
            "mbreqtime_0": ["5"],
            "mbreqtime_1": ["10"],
            "fboard": ["EP"],
            "aerostart": [""],
            "imma": ["M3"],
            "media": [""],
            "pmonopos": ["d"],
            "nvol": ["N3"],
            "coms": ["Tapez ici vos commentaires"],
            "aeroend": [""],
            "vaitime_1": [""],
            "vaitime_0": [""],
            "passengerB": [""],
            "passengerC": [""],
            "landingcount": [""],
            "passengerA": [""],
            "date": ["04/07/2011"],
            "takeoffcount": [""],
            "mbreqdn": ["n"],
            "ifr": [""],
            "log_id": ["1"],
            "simu_0": [""],
            "pmonodn": ["n"],
            "simu_1": [""],
            "obs": ["Tapez ici les observations"],
        }
        resp = self.c.post(reverse("logbooks:edit_log", args=[logbook.pk, log1.pk]), data, follow=True)
        self.assertEqual(resp.status_code, 200)

        # edit was a success ?
        updated_log1 = DGACAvionLog.objects.get(pk=log1.pk)
        self.assertEqual(updated_log1.aeronef_type, "T1-edit")

        new_log1_date = updated_log1.date
        new_log1_cdate = updated_log1.cdate

        # Cdate hh:mm:ss and date hh:mm:ss Should be different !
        self.assertEqual(log1_cdate, new_log1_cdate)
        self.assertEqual(log1_date, new_log1_date)

    def test_report_totals_no_cache(self):
        # Create a log book
        patch_settings(CACHING=False)
        self._report_totals_cache_helper_test()

    def test_report_totals_cache(self):
        # Create a log book
        patch_settings(CACHING=True)
        self._report_totals_cache_helper_test()

    def _report_totals_cache_helper_test(self):
        data = {"plane_dgac": 1}
        resp = self.c.post(reverse("logbooks:addlogbook"), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(LogBookBase.objects.all()), 1)
        self.assertContains(resp, "DGAC Avion", 1)

        logbook = LogBookBase.objects.all()[0]

        # Add a log 2h (120) on  mono nuit double
        log1 = DGACAvionLog(
            lbook=logbook,
            date=datetime(year=2011, month=1, day=10),
            cdate=datetime.now(),
            update=datetime.now(),
            aeronef_type="T1",
            aeronef_imma="IMM1",
            fctbrd="EP",
            natvol="foo",
            mbr_equipage_jour=0,
            mbr_equipage_nuit=0,
            mono_jdbl=0,
            mono_jcdb=0,
            mono_ndbl=0,
            mono_ncdb=120,
            mul_jdbl=0,
            mul_jcdb=0,
            mul_jcplt=0,
            mul_ndbl=0,
            mul_ncdb=0,
            mul_ncplt=0,
            vai_dbl=0,
            vai_plt=0,
            simu=0,
            ifr=0,
            obs="",
            cmmts="",
            nbrto=0,
            nbrla=0,
            airpdep="",
            airpar="",
            staffob="",
            optional_filter="",
        )
        log1.save()

        # go to logbook page and try to look for mono_ncdb 2:00
        resp = self.c.get(reverse("logbooks:logbook", kwargs={"logbook_id": logbook.pk}), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'data-field="mono_ncdb" class="e ttime_0 c10">2:00', 1)

        # Add an earlier log nbr 2 with 4h en mono nuit cdt bord
        log2 = DGACAvionLog(
            lbook=logbook,
            date=datetime(year=2008, month=1, day=10),
            cdate=datetime.now(),
            update=datetime.now(),
            aeronef_type="T1",
            aeronef_imma="IMM1",
            fctbrd="EP",
            natvol="foo",
            mbr_equipage_jour=0,
            mbr_equipage_nuit=0,
            mono_jdbl=0,
            mono_jcdb=0,
            mono_ndbl=0,
            mono_ncdb=240,
            mul_jdbl=0,
            mul_jcdb=0,
            mul_jcplt=0,
            mul_ndbl=0,
            mul_ncdb=0,
            mul_ncplt=0,
            vai_dbl=0,
            vai_plt=0,
            simu=0,
            ifr=0,
            obs="",
            cmmts="",
            nbrto=0,
            nbrla=0,
            airpdep="",
            airpar="",
            staffob="",
            optional_filter="",
        )
        log2.save()

        # go to logbook page and try to for the end value of total fly time (bottom)
        resp = self.c.get(reverse("logbooks:logbook", kwargs={"logbook_id": logbook.pk}), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'data-field="mono_ncdb" class="reports-info">4:00', 1)

    def test_rename_logbook_deleted(self):
        delete_lbook_form = DeleteLbookForm()
        logbook = self._create_logbook()
        self.assertEqual(logbook.name, "Avion DGAC")
        delete_lbook_form.delete(logbook, UserProfile.objects.get(user_id=logbook.ownr_id))
        self.assertEqual(logbook.deleted, True)
        self.assertEqual(logbook.name, "Deleted_Avion DGAC")

        logbook_copy = self._create_logbook()
        self.assertEqual(logbook_copy.name, "Avion DGAC")
        delete_lbook_form.delete(logbook_copy, UserProfile.objects.get(user_id=logbook.ownr_id))
        self.assertEqual(logbook_copy.deleted, True)
        self.assertEqual(logbook_copy.name, "Deleted_Avion DGAC(1)")
