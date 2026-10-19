"""
# Height_format

Internally we store height as an pieds
The goal of time_format is to provide a set of tools to seamlessly display and
prompt height values in different formats.
"""

from django import forms


class MeterFormatter:
    @staticmethod
    def output(cmeters, **kwargs):
        """
        The output method does the (meters -> feets) conversion.
        """
        return int(round(int(cmeters) / 100))

    @staticmethod
    def input(custom_format, **kwargs):
        """
        The input method does the (pieds -> meters) conversion.
        """
        return int(round(int(custom_format) * 100))


class FeetFormatter:
    @staticmethod
    def output(feets, **kwargs):
        """
        The output method
        """
        return int(round(feets / 30.48))

    @staticmethod
    def input(custom_format, **kwargs):
        """
        The input method does the (meters -> feets) conversion.
        """
        return int(round(int(custom_format) * 30.48))


class MeterWidget(forms.widgets.TextInput):
    def __init__(self, **attrs):
        if "class" not in attrs.keys():
            attrs["class"] = "input-small"
        super().__init__(attrs)

    def _format_value(self, value):
        try:
            val = MeterFormatter.output(value)
        except ValueError, TypeError:
            val = value
        return val


class MeterField(forms.fields.Field):
    widget = MeterWidget

    def __init__(self, **kwargs):
        initdata = {
            "widget": kwargs.get("widget", MeterWidget),
            "label": kwargs.get("label"),
            "initial": kwargs.get("initial"),
            "help_text": kwargs.get("help_text", ""),
            "required": kwargs.get("required", False),
        }
        super().__init__(**initdata)

    def to_python(self, value):
        if value == "":
            value = "0"
        try:
            int(value)
        except ValueError:
            msg = "Format incorrect, integer required"
            raise forms.ValidationError(msg)
        else:
            return MeterFormatter.input(value)


class FeetWidget(forms.widgets.TextInput):
    def __init__(self, **attrs):
        if "class" not in attrs.keys():
            attrs["class"] = "input-small"
        super(MeterWidget, self).__init__(attrs)

    def _format_value(self, value):
        try:
            val = FeetFormatter.output(value)
        except ValueError, TypeError:
            val = value
        return val


class FeetField(forms.fields.Field):
    widget = FeetWidget

    def __init__(self, **kwargs):
        initdata = {
            "widget": kwargs.get("widget", MeterWidget),
            "label": kwargs.get("label"),
            "initial": kwargs.get("initial"),
            "help_text": kwargs.get("help_text", ""),
            "required": kwargs.get("required", False),
        }
        super().__init__(**initdata)

    def to_python(self, value):
        if value == "":
            value = "0"
        try:
            int(value)
        except ValueError:
            msg = "Format incorrect, integer required"
            raise forms.ValidationError(msg)
        else:
            return FeetFormatter.input(value)


HEIGHT_MAPPING = (
    ("mètres", MeterFormatter, MeterField),
    ("pieds", FeetFormatter, FeetField),
    # ('Canadian', CanadianFormatter, CanadianField),
)

HEIGHT_FORMAT_CHOICES = tuple((i, HEIGHT_MAPPING[i][0]) for i in range(len(HEIGHT_MAPPING)))


def get_field(logbook):
    """
    Helper for forms. Returns the correct form field for the given logbook.
    """
    return HEIGHT_MAPPING[logbook.height_format][2]
