import pathlib
from os import listdir, path, system

from django.contrib.auth.models import User
from django.test import TestCase

from cloudy.core.utils import count_files, patch_settings
from cloudy.DGAC_avion_logbook.models import DGACAvionLogBook
from cloudy.DGAC_planeur_logbook.models import DGACPlaneurLogBook
from cloudy.FCL1080.models import FCL1080LogBook
from cloudy.FFP_logbook.models import FFPLogBook
from cloudy.FFPLUM_ulm_logbook.models import FFPLUMUlmLogBook
from cloudy.imports.models import Import
from cloudy.logbooks.models import LogBookBase

MAIL_PATH = "/tmp/testing_cloudy_imports_mails"

SETTINGS = {
    "EMAIL_BACKEND": "django.core.mail.backends.filebased.EmailBackend",
    "EMAIL_FILE_PATH": MAIL_PATH,
}


def mail_contains(data):
    """Check if `data` is contained in the mail"""
    f = pathlib.Path(path.join(MAIL_PATH, listdir(MAIL_PATH)[0])).open()
    c = f.read()
    return data in c


class ImportsNotificationTest(TestCase):
    """
    Check that the imports actions are correctly notified.
    """

    fixtures = ["imports_accounts.json"]

    def setUp(self):
        system(f"rm -Rf {MAIL_PATH} && mkdir -p {MAIL_PATH}")

        admin = User.objects.get(email="importer@example.com")
        dummy_user = User.objects.get(email="pilot@example.com")
        self.logbook = LogBookBase(ownr=dummy_user)
        self.logbook.save()
        data = {
            "owner": admin,
            "import_state": 1,
            "logbook_state": 0,
            "user": dummy_user,
            "logbook": self.logbook,
            "comments": "",
            "file_name": "screwyougys.mov",
        }
        self.imp = Import(**data)

    def tearDown(self):
        self.imp.pk is None or self.imp.delete()
        self.logbook.delete()

    def test_new_import(self):
        """Imports added."""
        with patch_settings(**SETTINGS):
            self.imp.save()

        sent_mails = count_files(MAIL_PATH)

        self.assertEqual(sent_mails, 1)
        self.assertTrue(mail_contains("importer@example.com"))
        self.assertTrue(mail_contains(self.imp.get_absolute_url()))

    def test_change_import(self):
        """Import reasigned."""
        self.imp.save()

        other_admin = User.objects.get(email="reviewer@example.com")
        self.imp.owner = other_admin

        with patch_settings(**SETTINGS):
            self.imp.save()

        sent_mails = count_files(MAIL_PATH)

        self.assertEqual(sent_mails, 1)
        self.assertTrue(mail_contains("To: reviewer@example.com"))
        self.assertTrue(mail_contains(self.imp.get_absolute_url()))


class ImportSamplesTest(TestCase):
    """
    Create some logbooks and import real-world CSVs known to work.
    """

    fixtures = ["imports_accounts.json"]

    def test_imports(self):
        mapping = {
            "AVION": DGACAvionLogBook,
            #'BALLON': DGACBallonLogBook,
            "FCL_PLANE": FCL1080LogBook,
            "PLANEUR": DGACPlaneurLogBook,
            "ULM": FFPLUMUlmLogBook,
            "PARACHUTE": FFPLogBook,
        }

        csvs_path = path.join(path.dirname(path.abspath(__file__)), "fixtures", "csvs")

        user = User.objects.get(email="pilot@example.com")

        for directory_name, logbook_class in mapping.items():
            class_csvs_path = path.join(csvs_path, directory_name)
            csv_files = listdir(class_csvs_path)

            for filename in csv_files:
                if not filename.endswith(".csv"):
                    continue

                time_in_min = False
                if "_minute" in filename:
                    time_in_min = True

                csv_file_path = path.join(class_csvs_path, filename)
                logbook = logbook_class(ownr=user, name=f"{directory_name}_{filename}")
                logbook.save()

                msg = logbook.import_from_csv(csv_file_path, delimiter=";", time_in_min=time_in_min)

                fd = pathlib.Path(csv_file_path).open()
                empty_line_len = len(logbook.csv_rules())

                # don't have to count the headers line
                i = -1
                for l in fd:
                    # empty row doesn't count
                    if not (len(l) == 0 or len(l) == empty_line_len):
                        i += 1
                fd.close()

                logbook = LogBookBase.get_by_id(logbook.pk)

                nbr_logs = logbook._log_model().objects.filter(lbook=logbook).count()
                self.assertEqual(msg["success"], True)
                self.assertEqual(nbr_logs, i)


class ImportTestError(TestCase):
    """
    Create some logbooks with error during import
    """

    fixtures = ["imports_accounts.json"]

    def test_time_error(self):
        user = User.objects.get(email="pilot@example.com")

        csv_error_path = path.join(path.dirname(path.abspath(__file__)), "fixtures", "csvs")
        filename = "import_time_error.csv"
        path_file = path.join(csv_error_path, filename)

        logbook = DGACAvionLogBook(ownr=user, name="%s" % (filename))

        msg = logbook.import_from_csv(path_file, delimiter=";", time_in_min=False)

        self.assertIn("ne valid pas le format HH:MM ou MM", msg["message"])

    def test_empty_error(self):
        user = User.objects.get(email="pilot@example.com")

        csv_error_path = path.join(path.dirname(path.abspath(__file__)), "fixtures", "csvs")
        filename = "import_empty_date_error.csv"
        path_file = path.join(csv_error_path, filename)

        logbook = DGACAvionLogBook(ownr=user, name="%s" % (filename))

        msg = logbook.import_from_csv(path_file, delimiter=";", time_in_min=False)

        self.assertIn("ne doit pas être vide", msg["message"])

    def test_date_format_error(self):
        user = User.objects.get(email="pilot@example.com")

        csv_error_path = path.join(path.dirname(path.abspath(__file__)), "fixtures", "csvs")
        filename = "import_format_date_error.csv"
        path_file = path.join(csv_error_path, filename)

        logbook = DGACAvionLogBook(ownr=user, name="%s" % (filename))

        msg = logbook.import_from_csv(path_file, delimiter=";", time_in_min=False)

        self.assertIn("ne valid pas le format d'une date XX/XX/XXXX", msg["message"])

    def test_column_error(self):
        user = User.objects.get(email="pilot@example.com")

        csv_error_path = path.join(path.dirname(path.abspath(__file__)), "fixtures", "csvs")
        filename = "import_column_error.csv"
        path_file = path.join(csv_error_path, filename)

        logbook = DGACAvionLogBook(ownr=user, name="%s" % (filename))

        msg = logbook.import_from_csv(path_file, delimiter=";", time_in_min=False)

        self.assertIn("Le nombre de colonnes ne correspond pas", msg["message"])
