import pathlib
from datetime import datetime
from os import path

from django.contrib.auth.models import User
from django.core.files import File
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from cloudy.core.models import FileModel
from cloudy.DGAC_avion_logbook.models import DGACAvionLog, DGACAvionLogBook


class StaticViewsTestCase(TestCase):
    """
    Test the status of the static views (only 200).
    """

    def setUp(self):
        self.c = Client()

    def test_home(self):
        url = reverse("home")
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_features(self):
        url = reverse("features")
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_gcu(self):
        url = reverse("gcu")
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_cgvu(self):
        url = reverse("cgvu")
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode()
        self.assertIn("AGPL-3.0", body)
        self.assertIn("https://github.com/Natim/cloudy", body)
        self.assertNotIn("tenter d’accéder aux codes-sources", body)

    def test_pricing(self):
        url = reverse("pricing")
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_support(self):
        url = reverse("support")
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_press(self):
        url = reverse("press")
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_crew(self):
        url = reverse("crew")
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_contactus(self):
        url = reverse("contactus")
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_fly_green_aviation(self):
        url = reverse("fly_green_aviation")
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode()
        self.assertIn("Fly Green Aviation", body)
        self.assertIn("mûrissement", body)
        self.assertIn("https://www.fly-green-aviation.com/", body)

    def test_air_avion(self):
        url = reverse("landing", kwargs={"aeronef": "avion"})
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_air_planeur(self):
        url = reverse("landing", kwargs={"aeronef": "planeur"})
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_air_helicoptere(self):
        url = reverse("landing", kwargs={"aeronef": "helicoptere"})
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_air_parachute(self):
        url = reverse("landing", kwargs={"aeronef": "parachute"})
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_air_ulm(self):
        url = reverse("landing", kwargs={"aeronef": "ulm"})
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_air_ballon(self):
        url = reverse("landing", kwargs={"aeronef": "ballon"})
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_partners_asf(self):
        url = reverse("partners", kwargs={"partner": "asf"})
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_partners_acafn(self):
        url = reverse("partners", kwargs={"partner": "acafn"})
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_partners_ffplum(self):
        url = reverse("partners", kwargs={"partner": "ffplum"})
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_partners_aeroweb(self):
        url = reverse("partners", kwargs={"partner": "aeroweb"})
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_partners_iaagepag(self):
        url = reverse("partners", kwargs={"partner": "iaagepag"})
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_partners_cercleaero(self):
        url = reverse("partners", kwargs={"partner": "cercleaero"})
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_partners_resair(self):
        url = reverse("partners", kwargs={"partner": "resair"})
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_partners_aecf(self):
        url = reverse("partners", kwargs={"partner": "aecf"})
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_partners_atmosky(self):
        url = reverse("partners", kwargs={"partner": "atmosky"})
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)


class UploadedFiles(TestCase):
    fixtures = ["testing_data.json"]

    def setUp(self):
        self.user = User.objects.get(pk=2)
        self.logbook = DGACAvionLogBook(ownr=self.user)
        self.logbook.save()

        local_path = path.dirname(path.abspath(__file__))
        superman = path.join(local_path, "fixtures", "Superman.jpg")
        self.f = pathlib.Path(superman).open("rb")
        self.test_picture = File(self.f)

    def tearDown(self):
        self.logbook.delete()
        self.f.close()

    def test_create_log(self):
        self.log = DGACAvionLog(
            lbook=self.logbook,
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
        self.log.save()

        fo = FileModel(file=self.test_picture, owner=self.user)
        fo.save()

        self.log.files.add(fo)
        self.log.save()

        self.assertEqual(self.user.filemodel_set.count(), 1)
        self.assertEqual(self.user.userprofile.disk_space_balance, int(self.test_picture.size))

    def test_delete_log(self):
        self.test_create_log()
        self.log.deleted = True
        self.log.save()

        balance = User.objects.get(pk=2).userprofile.disk_space_balance
        self.assertEqual(balance, 0)
