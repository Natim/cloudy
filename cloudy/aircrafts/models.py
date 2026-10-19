# Django imports {{{
from django.core.exceptions import ValidationError
from django.db import models

from cloudy.core.models import FileModel

# }}}
# Cloudy {{{
from cloudy.logbooks.models import LogBookBase

# }}}


class Aircraft(models.Model):
    logbook = models.ForeignKey(LogBookBase, on_delete=models.CASCADE)
    imma = models.CharField("Immatriculation", max_length=50)
    type = models.CharField("Type", max_length=128, blank=True, null=True)
    pictures = models.ManyToManyField(FileModel, blank=True)
    airport = models.CharField("Aéroport", max_length=200, blank=True, null=True)

    def get_photo(self):
        pics = self.pictures.all()
        nbr = len(pics)
        if nbr == 0:
            return None
        else:
            return pics[nbr - 1].file

    def clean(self):
        """
        Check for unicity + Check max for eco plan (currently 1).

        Legally, each aircraft has its own immatriculation. However, because
        users can do silly things such as typos and providing fake data, we
        cannot enforce the unicity of the immatriculation field throughout the
        database. So we check that each user cannot have two aircrafts with
        the same immatriculation.
        However, as logbook is an M2M, we cannot use unique_together. We will
        need to enforce this by overriding the clean() method.
        """

        # If the aircraft is not yet created, we attribute a negative PK so as
        # it won't match any of the records during the tests.
        pk = getattr(self, "pk", -1)
        pk = -1 if pk is None else pk

        if (
            not self.logbook.ownr.userprofile.has_payed_plan()
            and pk == -1
            and Aircraft.objects.filter(logbook=self.logbook).count() >= 1
        ):
            raise ValidationError(
                "Vous devez souscrire à l'offre First Class afin de pouvoir enregistrer plus d'un aéronef."
            )

        # Retrieve possible matches.
        seems = Aircraft.objects.filter(logbook=self.logbook, imma__iexact=self.imma)
        count = len(seems)

        # If no aircraft is registered it's OK anyway.
        if count == 0:
            return

        # Otherwise we check that the first (and theoretically the sole) aircraft
        # is the one we are checking. (in case of editing)
        if not seems[0].pk == pk:
            raise ValidationError(
                "Vous ne pouvez pas posséder deux aéronefs avec la même immatriculation sure le même carnet."
            )
