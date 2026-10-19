from django import forms

from . import get_field


class BaseTimeFormattedForm(forms.Form):
    def __init__(self, logbook, *args, **kwargs):
        super().__init__(logbook, *args, **kwargs)
        time_field = get_field(logbook)

        for name, options in self.timefields.items():
            attributes = {
                "label": options[0],
                "required": options[1],
                "max_hours": None,
            }
            self.fields[name] = time_field(**attributes)
