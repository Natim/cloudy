from django.db import models


class OptionalFilterChoice(models.Model):
    short_name = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=30)

    def __unicode__(self):
        return self.short_name


class FfpOptionalFilterChoice(models.Model):
    short_name = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=30)

    def __unicode__(self):
        return self.short_name
