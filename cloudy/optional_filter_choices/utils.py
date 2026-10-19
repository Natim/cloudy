"""Choice callables for the "optional filter" form fields.

These used to be module-level lists built by querying at import time, which froze
the values for the life of the process and made merely importing the module fail
before the tables existed. forms.ChoiceField accepts a callable and re-evaluates it
whenever the choices are rendered, so the queries happen per-request instead.
"""

from .models import FfpOptionalFilterChoice, OptionalFilterChoice


def optional_filter_choices():
    return [(choice.short_name, choice.name) for choice in OptionalFilterChoice.objects.all()]


def ffp_optional_filter_choices():
    return [(choice.short_name, choice.name) for choice in FfpOptionalFilterChoice.objects.all()]
