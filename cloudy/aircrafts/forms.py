# Django {{{
from django import forms

# }}}
# Cloudy {{{
from .models import Aircraft

# }}}


class AircraftForm(forms.ModelForm):
    pictures = forms.FileField(label="Image", required=False)

    def clean_imma(self):
        data = self.cleaned_data["imma"]
        return data.upper()

    class Meta:
        model = Aircraft
        widgets = {
            "logbook": forms.HiddenInput(),
            "imma": forms.TextInput(attrs={"class": "input-medium"}),
            "type": forms.TextInput(attrs={"class": "input-medium"}),
            "airport": forms.TextInput(attrs={"class": "input-medium"}),
        }
        fields = "__all__"
