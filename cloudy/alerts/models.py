# System imports {{{
import json

from django.contrib.auth.models import User

# }}}
# Django imports {{{
from django.db import models

from cloudy.logbooks.models import LogBookBase

# }}}
# Cloudy {{{
from ..core.utils import upload_to

# }}}

# Data {{{
ALERT_CHOICES = (("sms", "SMS"), ("email", "Email"))
QUALIFICATION_CATEG = (("qualification", "Qualification"), ("medical", "Medical"))
QUALIFICATION_SUB_TYPES = (
    ("plane", "Avion"),
    ("glider", "Planeur"),
    ("copter", "Helicopter"),
    ("ulm", "ULM"),
    ("blimp", "Ballon"),
)
QUALIFICATION_TYPES = (
    ("w_expiry", "Qualifications avec date d'expiration"),
    ("wo_expiry", "Licences et qualifications sans date d'expiration"),
    ("class_type", "Qualifications de classe et de type"),
)
QUALIFICATION_GLISSANTE_SUB_TYPES = (
    ("plane", "Avion"),
    ("glider", "Planeur"),
    ("copter", "Helicopter"),
    ("ulm", "ULM"),
    ("para", "Parachute"),
)
# }}}


class QualificationType(models.Model):
    categ = models.CharField(max_length=20, choices=QUALIFICATION_CATEG)
    type = models.CharField(max_length=20, choices=QUALIFICATION_TYPES)
    sub_type = models.CharField(max_length=20, choices=QUALIFICATION_SUB_TYPES, blank=True, null=True)
    name = models.CharField(max_length=200)
    duration = models.CharField(max_length=20)

    def to_json(self):
        data = {
            "categ": self.categ,
            "type": self.type,
            "sub_type": self.sub_type,
            "name": self.name,
            "duration": self.duration,
        }
        return json.dumps(data)

    def __str__(self):
        return f"{self.categ} {self.type} {self.name}"


class Qualification(models.Model):
    # Fields {{{
    # Owner id (I hate 'ownr', but let's stay consistent...)
    ownr = models.ForeignKey(User, on_delete=models.CASCADE)

    license_type = models.ForeignKey(QualificationType, on_delete=models.CASCADE)

    photo = models.ImageField(upload_to=upload_to("qualifications/pictures"), null=True, blank=True)

    expiry_date = models.DateField(default=None, blank=True, null=True)
    achievement_date = models.DateField(blank=False)
    # }}}

    def _has_alert(self, atype):
        return self.alert_set.filter(kind=atype).count() > 0

    def has_any_alert(self):
        return self.alert_set.all().count() > 0

    def has_email_alert(self):
        return self._has_alert("email")

    def has_sms_alert(self):
        return self._has_alert("sms")

    def days_before(self):
        return list(self.alert_set.all())[0].days_before

    class Meta:
        unique_together = ("ownr", "license_type")

    def __unicode__(self):
        return f"{self.ownr} {self.license_type}"


class Alert(models.Model):
    # Fields {{{
    qualification = models.ForeignKey(Qualification, on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=ALERT_CHOICES)
    days_before = models.IntegerField(default=7)
    sent = models.BooleanField(default=False)
    # }}}

    def __unicode__(self):
        return f"{self.qualification} sent ? {self.sent}"


class QualificationGlissanteType(models.Model):
    category = models.CharField(
        max_length=20, choices=QUALIFICATION_GLISSANTE_SUB_TYPES, blank=False, null=False
    )
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return f"{self.category} {self.name}"


class QualificationGlissante(models.Model):
    ownr = models.ForeignKey(User, on_delete=models.CASCADE)
    license_type = models.ForeignKey(QualificationGlissanteType, on_delete=models.CASCADE)
    loogbook = models.ForeignKey(LogBookBase, on_delete=models.CASCADE)

    experience_int = models.IntegerField()
    experience_unity = models.CharField(max_length=50)
    duree_int = models.IntegerField()
    duree_unity = models.CharField(max_length=5)

    def __unicode__(self):
        return f"{self.ownr} {self.license_type}"


class AlertGlissante(models.Model):
    qualif = models.ForeignKey(QualificationGlissante, on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=ALERT_CHOICES, default="email")
    days_before = models.IntegerField(default=30)
    sent = models.BooleanField(default=False)
    last_value = models.IntegerField(default=0)
