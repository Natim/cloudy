from django.contrib.auth.models import User
from django.db import models

from cloudy.payment.signals import (
    free_registration_complete,
    upgrade_plan_complete,
)
from cloudy.payment.tasks import post_free_registration, post_payed_upgrade

STATES = (
    (0, "not authorized"),
    (1, "authorized"),
    (2, "rejected"),
    (3, "accepted"),
)


def pdf_filename(instance, filename):
    return f"invoice_{instance.uuid}.pdf"


class OrderInvoice(models.Model):
    uuid = models.IntegerField()
    created_date = models.DateTimeField(auto_now_add=True)
    label = models.CharField(max_length=512)
    pdf = models.FileField(upload_to=pdf_filename)
    sent = models.BooleanField(default=False)


class PaymentOrderManager(models.Manager):
    def for_user(self, user):
        return self.get_queryset().filter(user=user, state=3).order_by("date")


class PaymentOrder(models.Model):
    uuid = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    state = models.IntegerField(choices=STATES)
    amount = models.IntegerField()
    number_of_months = models.IntegerField(default=12)
    promo_code = models.CharField(max_length=10, blank=True)
    discount_amount = models.IntegerField(default=0, blank=True, null=True)
    authcard_holder = models.CharField(max_length=150, blank=True)
    authnbr = models.CharField(max_length=50, blank=True)
    authcode = models.CharField(max_length=6, blank=True)
    authmsg = models.CharField(max_length=150, blank=True)
    transid = models.CharField(max_length=50, blank=True, null=True)
    invoice = models.ForeignKey(OrderInvoice, blank=True, null=True, on_delete=models.CASCADE)

    objects = PaymentOrderManager()

    def __str__(self) -> str:
        return f"UUID:{self.uuid} AMOUNT: {self.amount / 100} E"


class ProcessedStripeEvent(models.Model):
    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=128)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Processed Stripe event"


free_registration_complete.connect(post_free_registration, dispatch_uid="post-free-registration")
upgrade_plan_complete.connect(post_payed_upgrade, dispatch_uid="post-payed-update")
