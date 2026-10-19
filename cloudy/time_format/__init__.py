"""
# Time_format

Internally we store times as an integer, representing an amount of minutes.
The goal of time_format is to provide a set of tools to seamlessly display and
prompt time values in different formats.
"""

from .formatters import HhmmFormatter, TenthFormatter
from .widgets import HhmmField, TenthField

TIME_MAPPING = (
    ("HH:MM", HhmmFormatter, HhmmField),
    ("Dixième", TenthFormatter, TenthField),
    # ('Canadian', CanadianFormatter, CanadianField),
)

TIME_FORMAT_CHOICES = tuple((i, TIME_MAPPING[i][0]) for i in range(len(TIME_MAPPING)))


def get_field(logbook):
    """
    Helper for forms. Returns the correct form field for the given logbook.
    """
    return TIME_MAPPING[logbook.time_format][2]
