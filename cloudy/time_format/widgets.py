from django import forms

from .formatters import HhmmFormatter, TenthFormatter


# Tenth {{{
class TenthWidget(forms.widgets.TextInput):
    def __init__(self, **attrs):
        if "class" not in attrs.keys():
            attrs["class"] = "input-small"
        super().__init__(attrs)

    def _format_value(self, value):
        try:
            val = TenthFormatter.output(value)
        except ValueError, TypeError:
            val = value
        if val == "0.0":
            val = ""
        return val


class TenthField(forms.fields.Field):
    widget = TenthWidget

    def __init__(self, **kwargs):
        initdata = {
            "widget": kwargs.get("widget", TenthWidget),
            "label": kwargs.get("label"),
            "initial": kwargs.get("initial"),
            "help_text": kwargs.get("help_text", ""),
            "required": kwargs.get("required", False),
        }
        super().__init__(**initdata)

    def to_python(self, value):
        if value == "":
            value = "0.0"
        try:
            float(value)
        except ValueError:
            msg = "Format incorrect. Examples : 5.3, 0.2, 1.0, 0.0"
            raise forms.ValidationError(msg)
        else:
            return TenthFormatter.input(value)


# }}}


# Canadian {{{
class CanadianWidget(forms.widgets.TextInput):
    pass


class CanadianField(forms.Field):
    pass


# }}}


# Hhmm {{{
class HhmmWidget(forms.widgets.MultiWidget):
    def __init__(self, attrs={"class": "input-small"}, required=False):
        widget = (forms.widgets.TextInput(), forms.widgets.TextInput())
        super().__init__(widget, attrs=attrs)

    def decompress(self, value):
        if value:
            hours, mins = HhmmFormatter.output(value).split(":")
            return [hours, mins]
        return [None, None]


class HhmmField(forms.MultiValueField):
    """
    Multi input form with two integer field one for hour and one for minutes
    """

    widget = HhmmWidget

    def __init__(self, required=False, widget=None, label=None, initial=None, help_text=None, max_hours=100):
        hours_field = forms.fields.IntegerField(max_value=max_hours, min_value=0, required=False)
        if max_hours == None:
            hours_field = forms.fields.IntegerField(min_value=0, required=False)

        field = (
            hours_field,
            forms.fields.IntegerField(max_value=59, min_value=0, required=False),
        )

        initdata = {
            "fields": field,
            "widget": widget,
            "label": label,
            "initial": initial,
            "help_text": help_text,
            "required": required,
        }

        super().__init__(**initdata)

    def compress(self, data_list):
        hours = data_list[0] if len(data_list) > 0 else 0
        mins = data_list[1] if len(data_list) > 1 else 0
        result = f"{hours}:{mins}"
        return HhmmFormatter.input(result)


# }}}
