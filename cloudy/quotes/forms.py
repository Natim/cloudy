"""
quotes.forms
~~~~~~~~~~~~

Form and validation code for quotes.

:author:	Randall Degges
:email:		rdegges@gmail.com
:license:	BSD, Randall Degges. Not covered by the AGPL at the repository root.
"""

from django import forms

from cloudy.quotes.models import Quote


class QuoteForm(forms.ModelForm):
    """Form for creating a new `Quote`."""

    class Meta:
        model = Quote
        # Django 1.8 made naming fields or exclude mandatory on a ModelForm.
        fields = "__all__"


class PublicQuoteForm(QuoteForm):
    """
    Form for submitting a new `Quote` to the pending approval queue. All
    `Quote` s created by this form will have public access only. This form
    allows the specification of the following fields only.

    ``author``
            [optional] The author of the `Quote` being submitted.

    ``quote``
            The quote to be stored.

    ``source``
            [optional] The source URL that the quote was found at. This provides a
            reference for anyone who later wishes to verify the authenticity of a
            specified `Quote`.
    """

    class Meta(QuoteForm.Meta):
        exclude = ["approved"]
