from django.contrib.auth.models import User
from django.db import models

COUPON_TYPES_CHOICE = (
    ("P", "percentage discount"),
    ("M", "miles"),
)


class Coupon(models.Model):
    code = models.CharField("Code promo", max_length=8, unique=True)
    reduc_type = models.CharField("Type", max_length=1, choices=COUPON_TYPES_CHOICE)
    created = models.DateTimeField(editable=False, auto_now_add=True)
    updated = models.DateTimeField(editable=False, auto_now=True)
    discount_value = models.IntegerField("Réduction")
    validity_end = models.DateTimeField("Date de fin")
    used = models.BooleanField("Usagé", default=False)
    number_of_users = models.IntegerField("Utilistaeurs", default=1)
    users = models.ManyToManyField(User, blank=True)

    class Meta:
        verbose_name = "Coupon"

    def __str__(self) -> str:
        return self.code
