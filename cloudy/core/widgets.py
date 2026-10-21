import re

from django import forms
from django.utils.translation import gettext_lazy as _

email_re = r"^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$"
# TODO django's email_re does not exists anymore


class MultiEmailField(forms.Field):
    def clean(self, value):
        regex = re.compile(email_re)
        if not value:
            raise forms.ValidationError(_("Entrez au moins une address email"))
        emails = value.split(",")
        emails = [x.strip() for x in emails]
        for email in emails:
            if not regex.search(email):
                raise forms.ValidationError(_("%s n'est pas une address valid" % email))
        if len(emails) > 50:
            raise forms.ValidationError(_("Pas plus de cinquante emails"))
        if len(emails) != len(set(emails)):
            raise forms.ValidationError(_("les emails doivent être différents"))
        return emails


class HorizontalRadioSelect(forms.RadioSelect):
    """Lays the radio buttons out on one line instead of stacking them.

    This used to be a RadioFieldRenderer passed as RadioSelect(renderer=...), an API
    Django 1.11 removed; radio layout is a template concern now, so the horizontal
    variant is a widget with its own template.
    """

    template_name = "core/widgets/horizontal_radio.html"
    option_template_name = "core/widgets/horizontal_radio_option.html"
