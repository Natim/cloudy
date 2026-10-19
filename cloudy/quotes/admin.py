"""
quotes.admin
~~~~~~~~~~~~

Provide admin panel integration hooks.

:author:    Randall Degges
:email:     rdegges@gmail.com
:license:   BSD, Randall Degges. Not covered by the AGPL at the repository root.
"""

from django.contrib import admin

from cloudy.quotes.models import Quote


class QuoteAdmin(admin.ModelAdmin):
    """Register our `Quote` model with the admin."""

    list_display = ("approved", "author", "quote", "source")


admin.site.register(Quote, QuoteAdmin)
