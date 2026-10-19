from django.db import models


class Article(models.Model):
    """Stores press"""

    date = models.DateField()
    title = models.CharField(max_length=250)
    reference = models.CharField(max_length=100)
    link = models.CharField(max_length=150)

    def __unicode__(self):
        return self.title
