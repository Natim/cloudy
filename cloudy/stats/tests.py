from datetime import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from cloudy.accounts.models import UserProfile
from cloudy.DGAC_avion_logbook.models import DGACAvionLog, DGACAvionLogBook
from cloudy.stats._common import END_DAY_TIME
from cloudy.stats.service import InvalidStatsDate, parse_time_slice


class ParseTimeSliceTest(TestCase):
    def test_rejects_malformed_begin_date(self):
        with self.assertRaises(InvalidStatsDate):
            parse_time_slice({"begin_date": "2026/05/02#", "end_date": "none"})

    def test_accepts_slash_begin_date(self):
        first, last = parse_time_slice({"begin_date": "2026/05/02", "end_date": "none"})
        self.assertEqual(first, datetime(2026, 5, 2))
        self.assertIsNone(last)

    def test_iso_custom_range_is_not_dayfirst_swapped(self):
        first, last = parse_time_slice({"begin_date": "2026-10-01", "end_date": "2026-10-30"})
        self.assertEqual(first, datetime(2026, 10, 1))
        self.assertEqual(last, datetime(2026, 10, 30, **END_DAY_TIME))


class GetTotalsReportsTest(TestCase):
    def setUp(self):
        user = User.objects.create_user("pilot", "pilot@example.com", "secret")
        UserProfile.objects.create(user=user, dob="1990-01-01")
        self.logbook = DGACAvionLogBook(
            ownr=user, name="Reports", cat="helicopter_dgac", update=timezone.now()
        )
        self.logbook.reports = {"mul_jcdb": 90}
        self.logbook.save()

        now = datetime.now()
        DGACAvionLog(
            lbook=self.logbook,
            date=datetime(2011, 7, 4),
            cdate=now,
            update=now,
            aeronef_type="AS355",
            aeronef_imma="F-GXXX",
            fctbrd="Cdb",
            natvol="",
            mbr_equipage_jour=0,
            mbr_equipage_nuit=0,
            mono_jdbl=0,
            mono_jcdb=0,
            mono_ndbl=0,
            mono_ncdb=0,
            mul_jdbl=0,
            mul_jcdb=30,
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
        ).save()

    def test_total_multi_day_captain_includes_report_and_logs(self):
        with_report = self.logbook.get_totals(
            ["total_multi_day_captain"], time_slice=(None, None), reports=True
        )
        without_report = self.logbook.get_totals(
            ["total_multi_day_captain"], time_slice=(None, None), reports=False
        )

        self.assertEqual(with_report["total_multi_day_captain"], 120)
        self.assertEqual(without_report["total_multi_day_captain"], 30)
