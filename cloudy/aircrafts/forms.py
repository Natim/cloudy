# Django {{{
from django import forms

# }}}
# Cloudy {{{
from .models import Aircraft

# }}}


class AircraftForm(forms.ModelForm):
    pictures = forms.FileField(label="Image", required=False)

    def __init__(self, *args, logbook=None, **kwargs):
        self._logbook = logbook
        super().__init__(*args, **kwargs)
        if logbook is not None:
            self.instance.logbook = logbook

    def clean_imma(self):
        data = self.cleaned_data["imma"]
        return data.upper()

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self._logbook is not None:
            obj.logbook = self._logbook
        if commit:
            obj.save()
            self.save_m2m()
        return obj

    class Meta:
        model = Aircraft
        widgets = {
            "imma": forms.TextInput(attrs={"class": "input-medium"}),
            "type": forms.TextInput(attrs={"class": "input-medium"}),
            "airport": forms.TextInput(attrs={"class": "input-medium"}),
        }
        fields = ("imma", "type", "airport")
