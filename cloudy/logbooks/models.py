# System imports {{{
import csv
import json
import pathlib
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder

# }}}
# Django imports {{{
from django.db import models, transaction
from django.urls import reverse

from cloudy import height_format, time_format
from cloudy.core.fields import DictionaryField
from cloudy.core.models import FileModel

# }}}
# Cloudy {{{
from cloudy.logbooks.csv_import import UnicodeReader, UnicodeWriter
from cloudy.stats.models import StatsModelBase

# }}}


# CSV Manipulation {{{
class StringHandler:  # {{{
    @classmethod
    def validate(cls, x, opts):
        if opts.get("empty", False):
            return True
        return isinstance(x, str)

    @classmethod
    def to_csv(cls, x, opts):
        return x

    @classmethod
    def from_csv(cls, x, opts):
        return x


# }}}


class IntHandler:  # {{{
    @classmethod
    def validate(cls, x, opts):
        if opts.get("empty", False):
            return True
        try:
            int(x)
        except ValueError:
            return False
        return True

    @classmethod
    def to_csv(cls, x, opts=None):
        if not x:
            x = ""
        return str(x)

    @classmethod
    def from_csv(cls, x, opts=None):
        return int(x)


# }}}


class BoolHandler:  # {{{
    @classmethod
    def validate(cls, x, opts):
        if opts.get("empty", False):
            return True
        try:
            int(x)
        except ValueError:
            return False
        if int(x) > 1 or int(x) < 0:
            return False
        return True

    @classmethod
    def to_csv(cls, x, opts=None):
        if x:
            return "1"
        return "0"

    @classmethod
    def from_csv(cls, x, opts=None):
        if x == "1":
            return True
        return False


# }}}


class TimeHandler:  # {{{
    @classmethod
    def validate(cls, x, opts):
        if opts.get("empty", False):
            return True
        if opts["time_in_min"]:
            # If time is in minutes only, it's just an integer
            return IntHandler.validate(x, opts)
        else:
            if ":" not in x:
                return False
            chunks = x.split(":")
            if not len(chunks) == 2:
                return False
            return IntHandler.validate(chunks[0], opts) and IntHandler.validate(chunks[1], opts)

    @classmethod
    def to_csv(cls, x, opts):
        if opts["time_in_min"] or opts.get("empty", False):
            return IntHandler.to_csv(x)  # We store it as a number of minutes
        else:
            if x == 0:
                return ""

            mins = x % 60
            hours = (x - mins) / 60

            # Add leading zeros
            if mins < 10:
                mins = "0%s" % mins
            if hours < 10:
                hours = "0%s" % hours

            return f"{hours}:{mins}"

    @classmethod
    def from_csv(cls, x, opts):
        tim = opts["time_in_min"]
        if tim:
            return IntHandler.from_csv(x)
        else:
            chunks = x.split(":")
            return int(chunks[0]) * 60 + int(chunks[1])


# }}}


class DateHandler:  # {{{
    @classmethod
    def validate(cls, x, opts):
        if opts.get("empty", False):
            return True

        sep = opts["date_separator"]

        if sep not in x:
            return False

        chunks = x.split(sep)

        if len(chunks) != 3:
            return False

        if not all(map(lambda x: IntHandler.validate(x, opts), chunks)):
            return False

        int_chunks = map(int, chunks)

        try:
            int_chunks.reverse()
            datetime(*int_chunks)
        except ValueError:
            return False

        return True

    @classmethod
    def to_csv(cls, x, opts):
        if not x:
            return ""
        sep = opts["date_separator"]
        return x.strftime("%d" + sep + "%m" + sep + "%Y")

    @classmethod
    def from_csv(cls, x, opts):
        sep = opts["date_separator"]
        chunks = x.split(sep)
        chunks = map(int, chunks)
        chunks.reverse()
        now = datetime.now()
        return now.replace(*chunks)


# }}}

TYPES = {
    "string": (StringHandler, "d'une chaîne de charactères"),
    "int": (IntHandler, "d'un entier"),
    "time": (TimeHandler, "HH:MM ou MM si vous avez sélectionné 'Temps en minutes'"),
    "date": (DateHandler, "d'une date XX/XX/XXXX"),
    "bool": (BoolHandler, "d'un booléen, vrai/faux ou 0/1"),
}


class CSVException(Exception):
    """Simple exception class to yield errors with an attached
    message."""

    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg


# }}}


class LogBookBase(StatsModelBase):  # TODO
    """Base logbook model with methods common to all logbooks."""

    # Fields {{{
    ownr = models.ForeignKey(User, on_delete=models.CASCADE)

    # Timestamps
    cdate = models.DateTimeField(blank=False, auto_now_add=True, db_index=True)
    update = models.DateTimeField(blank=False, db_index=True, db_column="udate")

    # Flags (no need for db_index
    # http://stackoverflow.com/questions/1844991/indexing-boolean-fields)
    visbl = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)

    # Category
    cat = models.CharField(max_length=128)

    # Name of the book unique with user id and category
    name = models.CharField(max_length=128)

    # Reports. We stock reports as JSON
    reports = DictionaryField(default={}, blank=True)

    # Content type is stored to retrieve the correct inherited instance
    content_type = models.ForeignKey(
        ContentType, editable=False, null=True, db_index=True, on_delete=models.CASCADE
    )

    # Time format (hh:mm, tenth...). Define the format used to output and input
    # times.
    time_format = models.IntegerField(default=0, choices=time_format.TIME_FORMAT_CHOICES)
    height_format = models.IntegerField(default=1, choices=height_format.HEIGHT_FORMAT_CHOICES)
    # }}}
    # Class methods {{{

    def save(self, *args, **kwargs):
        if not self.content_type:
            self.content_type = ContentType.objects.get_for_model(self.__class__)
        super().save(*args, **kwargs)

    def __unicode__(self):
        return f"{self.name} {self.cat}"

    # Selection {{{
    @classmethod
    def _for_user(cls, user):
        return (
            LogBookBase.objects.filter(ownr=user)
            .annotate(last_entry=models.Max("logbase__cdate"))
            .order_by("-last_entry")
        )

    @classmethod
    def active_for_user(cls, user):
        user = User.objects.get(pk=user)
        base_logbooks = LogBookBase._for_user(user).filter(visbl=True, deleted=False)
        return [x._cast() for x in base_logbooks]

    def _cast(self):
        content_type = self.content_type
        klass = content_type.model_class()
        return klass.objects.get(id=self.id)

    @classmethod
    def existing_for_user(cls, user):
        """
        Retrieve existing logbooks for the given user pk
        """
        base_logbooks = LogBookBase._for_user(user).filter(deleted=False)
        return [x._cast() for x in base_logbooks]

    @classmethod
    def for_user(cls, user):
        """
        Retrieve all logbooks for the given user pk
        """
        base_logbooks = LogBookBase._for_user(user)
        return [x._cast() for x in base_logbooks]

    @classmethod
    def get_by_id(cls, pk):
        try:
            base_logbook = LogBookBase.objects.get(pk=pk)
            return base_logbook._cast()
        except LogBookBase.DoesNotExist:
            # I think we should raise an error there.
            return None

    # }}}
    # CSV Manipulation {{{
    def attach_csv_to_http_response(self, http_response):
        """
        Return the logbook logs as a csv file
        Order logs by year
        """
        writer = UnicodeWriter(http_response, delimiter=";")

        headers = [x[4] for x in self.csv_rules()]
        writer.writerow(headers)

        for log in self.logs_qs():
            writer.writerow(self.create_row_from_log(log))

    def attach_pdf_to_http_response(self, http_response, title, show_cuts=False):
        """
        Attaches the logbook pdf as the http response object (if passed)
        """
        logs = list(self.logs_qs())
        self.pdf_gen_method()(http_response, title, show_cuts, logs, self.reports)

    def create_row_from_log(self, log, **kwargs):
        rules = self.csv_rules()

        options = {
            "time_in_min": False,
            "date_separator": "/",
        }
        options.update(kwargs)

        chunks = []

        for rule in rules:
            item = getattr(log, rule[0])
            rtype = rule[1]
            value = TYPES[rtype][0].to_csv(item, options)
            chunks.append(value)

        return chunks

    @property
    def can_fly(self):
        return True

    @transaction.atomic
    def import_from_csv(self, csv_path, delimiter=",", **kwargs):
        """
        Import LogBook entries from a CSV file
        Return a response dictionary of the form:
            {'success': True, 'count': n}
            or
            {'success': False, 'message': 'error'}

        Csv file should have:
        - Encoding: UTF-8
        - Text separator: "
        """

        options = {
            "time_in_min": False,
            "date_separator": "/",
        }
        options.update(kwargs)

        def validate_csv_row(row, rules):  # {{{
            """Validate a CSV row according to rules."""

            # Check length
            correct_length = len(rules)
            length = len(row)
            if not length == correct_length:
                raise CSVException(
                    "Le nombre de colonnes ne correspond pas :  %s au lieu de %s" % (length, correct_length)
                )

            # Validate the list

            for i in range(length):
                cell = row[i]
                rule = rules[i]
                ctype = rule[1]

                empty = not cell
                local_options = {"empty": empty}
                local_options.update(options)
                valid = TYPES[ctype][0].validate(cell, local_options)

                can_be_empty = rule[3]

                if empty and not can_be_empty:
                    raise CSVException("Le champ '%s' ne doit pas être vide" % rule[4])

                if not valid:
                    msg = f"Le champ '{rule[4]}' ne valid pas le format {TYPES[ctype][1]}"
                    raise CSVException(msg)

        # }}}

        def create_log_from_row(row, rules, time_in_min):  # {{{
            klass = self._log_model()

            data = {}

            for i in range(len(row)):
                cell = row[i]
                rule = rules[i]
                ctype = rule[1]
                empty = not cell
                value = rule[2]

                local_options = {"empty": empty}
                local_options.update(options)

                if not empty:
                    value = TYPES[ctype][0].from_csv(cell, local_options)

                data[rule[0]] = value

            return klass(lbook=self, cdate=datetime.now(), update=datetime.now(), **data)

        # }}}

        response = {"success": True}
        rules = self.csv_rules()

        # Prepare the reader object to read the uploaded CSV file.
        reader = UnicodeReader(pathlib.Path(csv_path).open(), delimiter=delimiter, quotechar='"')

        # We count line numbers to provide precise bug reports.
        line_num = 0

        # template empty row CSV
        empty_lines_tpl = []
        for i in range(len(rules)):
            empty_lines_tpl.append("")

        try:
            # We parse each line of the file.
            for row in reader:
                line_num += 1

                # We skip the first line because it's just headers
                # A row can be empty
                def cmp(a, b):  # Does not exist in Python 3.x
                    return (a > b) - (a < b)

                if line_num == 1 or not len(row) or not cmp(empty_lines_tpl, row):
                    continue

                # Check row validity
                validate_csv_row(row, rules)

                # Create log entry
                log = create_log_from_row(row, rules, options)
                # Save the log
                log.save()

        # Handle errors
        except (csv.Error, CSVException) as exp:
            response["success"] = False
            response["message"] = f"Erreur Ligne {line_num}: {exp.msg}"
        except UnicodeDecodeError as exp:
            response["success"] = False
            msg = f"Erreur Ligne {line_num}: {exp}"
            response["message"] = msg

        if response["success"]:
            response["count"] = line_num
            transaction.commit()
        else:
            transaction.rollback()

        return response

    # }}}

    @classmethod
    def rows_per_page(cls):
        return 14

    def logs_qs(self, time_slice=(None, None), filters={}, qs=[]):
        # We only want logs for the current logbook
        query = self._log_model().objects.filter(lbook=self)
        # We want active (visible) logs
        new_filters = {
            "visbl": True,
            "deleted": False,
        }

        # Add extra filters (if any)
        for key, value in filters.items():
            new_filters[str(key.replace(".", "__"))] = value

        # Add date filtering
        if time_slice[0] is not None:
            new_filters["date__gte"] = time_slice[0]
            # invalid fix #247
            # cut = time(0,0,0,0)
            # new_filters['date__gte'] = datetime.combine(time_slice[0].date(), cut)
        if time_slice[1] is not None:
            new_filters["date__lte"] = time_slice[1]
            # invalid fix #247
            # fill = time(23,59,59,999999)
            # new_filters['date__lte'] = datetime.combine(time_slice[1].date(), fill)

        return query.filter(*qs, **new_filters).order_by("date")

    @classmethod
    def check_unique_name(cls, log_book_class, user_id, name):
        """
        Return the logbook name as it is if unique for the given user
        otherwise return the name with count appended.
        foo
        foo (1) ...
        """
        user = User.objects.get(pk=user_id)
        while LogBookBase.objects.filter(ownr=user, name=name):
            try:
                split = name.split("(")
                name = split[0]
                inc = int(split[1][:-1])
            except IndexError, ValueError:
                inc = 0
            inc += 1
            name = f"{name}({inc})"
        return name

    # @models.permalink
    def get_absolute_url(self):
        return reverse("logbooks:home", args=[self.id])

    @property
    def time_format_str(self):
        return time_format.TIME_MAPPING[self.time_format][0]

    @property
    def height_format_str(self):
        return height_format.HEIGHT_MAPPING[self.height_format][0]

    @property
    def height_formatter(self):
        return height_format.HEIGHT_MAPPING[self.height_format][1]

    @property
    def time_formatter(self):
        return time_format.TIME_MAPPING[self.time_format][1]

    # }}}

    # To inherit {{{
    @classmethod
    def _log_model(cls):
        """
        Override me!
        Returns the model to use for log entries.
        """
        raise NotImplementedError

    @classmethod
    def _report_form_model(cls):
        raise NotImplementedError

    @classmethod
    def _log_form_model(cls):
        raise NotImplementedError

    def csv_rules(self):
        """
        Define import CSV validation rules.
        Must be a list of tuple matching the following pattern:

        (field_name, type, default, can_be_empty)
             ^         ^      ^         ^
           string   string   any     boolean

        * `field_name`: as named in the model definition.
        * `type`: one of ('string', 'int', 'date', 'time').
        * `default': really what ever you want.
        * `can_be_empty: a boolean which answers this question.
        """
        raise NotImplementedError

    def create_log_from_row(self, row):
        """
        Convert CSV row data to a logbook entry
        Return log
        """
        raise NotImplementedError

    def totals_rules(self):
        raise NotImplementedError

    def home_page_totals(self):
        raise NotImplementedError

    def totals_page_totals(self):
        raise NotImplementedError

    # }}}

    class Meta:
        unique_together = ("name", "ownr", "cat")
        ordering = ["-cdate"]


class LogBase(models.Model):  # TODO
    """Base log class."""

    # Fields {{{
    lbook = models.ForeignKey(LogBookBase, on_delete=models.CASCADE)

    # Timestamps
    # NO auto now add for create date as we control it's value ourself
    cdate = models.DateTimeField(blank=False, db_index=True)
    update = models.DateTimeField(blank=False, db_index=True, db_column="udate")

    # Flags
    visbl = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)

    # Date
    date = models.DateTimeField(blank=False, db_index=True)

    # Optional filter
    optional_filter = models.CharField(max_length=30, blank=False, db_index=True)

    # Media files
    files = models.ManyToManyField(FileModel)

    # Airport departure
    airpdep = models.CharField(max_length=200, db_index=True)
    # Airport  arrivals
    airpar = models.CharField(max_length=200, db_index=True)
    # }}}
    # To inherit {{{

    content_type = models.ForeignKey(
        ContentType, editable=False, null=True, db_index=True, on_delete=models.CASCADE
    )

    def _cast(self):
        content_type = self.content_type
        klass = content_type.model_class()
        return klass.objects.get(id=self.id)

    def save(self, *args, **kwargs):
        if not self.content_type:
            self.content_type = ContentType.objects.get_for_model(self.__class__)
        super().save(*args, **kwargs)

    def __unicode__(self):
        return "Log du %s" % (self.date)
        # raise NotImplementedError

    # }}}

    # Class methods {{{
    @classmethod
    def get_by_id(cls, pk):
        try:
            base_log = LogBase.objects.get(pk=pk)
            return base_log._cast()
        except LogBase.DoesNotExist:
            return None

    # }}}

    def json_rules(self):
        return [
            ("lbook", "fk"),
            ("id", "integer"),
            ("visbl", "bool"),
            ("deleted", "bool"),
            ("date", "date"),
            ("update", "date"),
            ("cdate", "date"),
            ("optional_filter", "string"),
        ]

    def to_json(self, serialize=True):
        "Return strings as Json"
        data = {}
        for rule in self.json_rules():
            rtype = rule[1]
            rname = rule[0]
            attr = getattr(self, rname)
            if rtype == "fk":
                data[rname] = attr.pk
            elif rtype == "bool":
                data[rname] = attr
            elif rtype == "date" and attr:
                data[rname] = attr.isoformat()
            elif rtype == "string":
                data[rname] = attr
            elif rtype == "integer":
                data[rname] = attr
            elif rtype == "list":
                data[rname] = attr

        # Add files
        data["files"] = []
        for f in self.files.all():
            data["files"].append({"path": f"{settings.MEDIA_URL}{f.file.name}"})

        if serialize:
            return json.dumps(data, cls=DjangoJSONEncoder)
        else:
            return data

    class Meta:
        ordering = ["-cdate"]
