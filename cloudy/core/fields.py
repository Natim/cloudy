# Honeypot {{{
# http://djangosnippets.org/snippets/131/
# In the following example, only the email field will be visible (the
# HoneypotFields are named as such to increase the chance that a bot
# will try to fill them in):
#
# class EmailForm(Form):
#    name = HoneypotField()
#    website = HoneypotField(initial='leave me')
#    email = EmailField()

import json

from django.forms import Field, TextInput, ValidationError

EMPTY_VALUES = (None, "")


class HoneypotWidget(TextInput):
    is_hidden = True

    def __init__(self, attrs=None, html_comment=False, *args, **kwargs):
        self.html_comment = html_comment
        super().__init__(attrs, *args, **kwargs)
        if "class" not in self.attrs:
            self.attrs["style"] = "display:none"

    def render(self, *args, **kwargs):
        value = super().render(*args, **kwargs)
        if self.html_comment:
            value = "<!-- %s -->" % value
        return value


class HoneypotField(Field):
    widget = HoneypotWidget

    def clean(self, value):
        if (self.initial in EMPTY_VALUES and value in EMPTY_VALUES) or value == self.initial:
            return value
        raise ValidationError("Anti-spam field changed in value.")


# }}}
# DictionaryField {{{
from django import forms
from django.core import exceptions
from django.db import models
from django.forms.utils import flatatt
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

# from django.utils.translation import ugettext_lazy as _
from django.utils.translation import gettext as _


class DictionaryField(models.Field):
    description = _("Dictionary object")
    default_error_messages = {
        "invalid": _("Value must be a JSON object."),
    }

    def get_internal_type(self):
        return "TextField"

    def _coerce_dict(self, value):
        if isinstance(value, dict):
            return value
        if value is None or value == "":
            return {}
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except (ValueError, TypeError) as exc:
                raise exceptions.ValidationError(self.error_messages["invalid"]) from exc
            if isinstance(parsed, dict):
                return parsed
        raise exceptions.ValidationError(self.error_messages["invalid"])

    def to_python(self, value):
        return self._coerce_dict(value)

    def from_db_value(self, value, expression, connection):
        # SubfieldBase used to call to_python() on load. Without this, the
        # column comes back as the stored JSON string and form code crashes
        # on initial.get().
        try:
            return self._coerce_dict(value)
        except exceptions.ValidationError:
            return {}

    def get_prep_value(self, value):
        if not value:
            return ""
        if isinstance(value, str):
            return value
        return json.dumps(value)

    def value_to_string(self, obj):
        return self.get_prep_value(self.value_from_object(obj))

    def formfield(self, **kwargs):
        defaults = {"widget": DictionaryWidget}
        defaults.update(kwargs)
        return super().formfield(**defaults)


# # rules for South migrations tool (for version >= 0.7)
# from south.modelsinspector import add_introspection_rules

# add_introspection_rules([], [r"^cloudy\.core\.fields\.DictionaryField"])


class DictionaryWidget(forms.widgets.TextInput):
    def render(self, name, value, attrs=None):
        if value is None:
            value = ""
        try:
            value = json.dumps(value)
        except:
            pass
        final_attrs = flatatt(self.build_attrs(attrs, name=name))
        final_value = conditional_escape(str(value))
        final_html = f"<textarea{final_attrs}>{final_value}</textarea>"
        return mark_safe(final_html)


# }}}
