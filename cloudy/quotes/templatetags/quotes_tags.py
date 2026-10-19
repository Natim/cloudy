"""
quotes.templatetags.quotes_tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Template tags to display quotes.

:author:    Randall Degges
:email:     rdegges@gmail.com
:license:   BSD, Randall Degges. Not covered by the AGPL at the repository root.
"""

from django import template
from django.core.exceptions import ObjectDoesNotExist

from cloudy.quotes.models import Quote

register = template.Library()


@register.inclusion_tag("quotes/quote.html")
def show_quote(quote_pk):
    """Display a single `Quote`."""

    try:
        quote = Quote.objects.get(pk=quote_pk)
    except ObjectDoesNotExist:
        quote = False

    return {"quote": quote}


@register.inclusion_tag("quotes/quote.html")
def show_random_quote():
    """Display a single random `Quote`."""

    try:
        quote = Quote.objects.order_by("?")[0]
    except IndexError:
        quote = False

    return {"quote": quote}


@register.inclusion_tag("quotes/quotes.html")
def show_all_quotes():
    """Display all quotes in random order."""
    quotes = Quote.objects.all()
    return {"quotes": quotes}
