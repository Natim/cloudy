"""
quotes.models
~~~~~~~~~~~~~

Provides Django websites with a simple way to store quotes.

:author:	Randall Degges
:email:		rdegges@gmail.com
:license:	BSD, Randall Degges. Not covered by the AGPL at the repository root.
"""

from django.db import models


class Quote(models.Model):
    """A memorable quote."""

    #: The default author used if none is specified during creation.
    DEFAULT_AUTHOR = "Unknown"

    author = models.CharField(
        blank=True, max_length=100, default=DEFAULT_AUTHOR, help_text="[optional] Quote author."
    )
    quote = models.TextField(help_text="A memorable quote.")
    source = models.URLField(blank=True, help_text="[optional] Quote source URL.")
    approved = models.BooleanField(help_text="Is this quote approved?")

    def __str__(self):
        return f"{self.author}: {self.quote}"

    def save(self, *args, **kwargs):
        """
        Override to automatically insert default author if none is specified.
        Usage::

                Specifying an author:

                >>> q = Quote.objects.create(author='rdegges', quote='test quote')
                >>> q.author == 'rdegges'
                True

                Not specifying an author:

                >>> q = Quote.objects.create(quote='test quote')
                >>> q.author == Quote.DEFAULT_AUTHOR
                True
        """
        if not self.pk and not self.author:
            self.author = self.DEFAULT_AUTHOR
        super().save(*args, **kwargs)
