import base64
import hashlib
import hmac
import random
from datetime import date, datetime, timedelta

from constance import config
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.utils import timezone

from cloudy.logbooks.models import LogBookBase

GENDER_CHOICES = (
    ("M", "M"),
    ("F", "F"),
)
# The higher, the more powerful.
# We can easily compare plans by indexing them with ints, not with letters.
PLAN_CHOICES = (
    (1, "Eco"),
    (2, "First class"),
)


def _avatar_path():
    return datetime.utcnow().strftime("avatars/%Y/%b/%d")


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField("gender", max_length=1, choices=GENDER_CHOICES, default="M")
    dob = models.DateField()

    postcode = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=60, blank=True)
    address = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=12, blank=True)  # Must be in the
    # international format
    miles_balance = models.IntegerField(default=0)
    month_balance = models.IntegerField(default=0)
    can_upload = models.BooleanField(default=True)

    disk_space_balance = models.IntegerField(default=0)

    plan = models.IntegerField("Plan", default=1, choices=PLAN_CHOICES)
    fplan_switch_date = models.DateTimeField("Switch to firstclass pack", blank=True, null=True)

    aerodrom = models.CharField("Aérodrome", max_length=70, blank=True)
    # avatar = models.ImageField(upload_to=upload_to(_avatar_path), blank=True, null=True)  # DELETE
    avatar = models.ImageField(upload_to=_avatar_path, blank=True, null=True)
    api_key = models.CharField(max_length=50, unique=True, blank=True, null=True)

    stripe_customer_id = models.CharField(max_length=255, blank=True, default="")
    stripe_subscription_id = models.CharField(max_length=255, blank=True, default="")

    iphone_free_use_date_start = models.DateField(
        "Date the free iphone app started to be used", blank=True, null=True
    )

    cgv_date = models.DateField("Signup CGV", default=date.today)

    def __init__(self, *args, **kwargs):
        """
        Add has_book_avion, has_book_* methods to the profile.
        """
        for book_type in settings.LOG_BOOKS_TYPE:
            setattr(self, "has_book_%s" % book_type, self.has_logbook_of_type(book_type))
        super().__init__(*args, **kwargs)

    def __unicode__(self):
        return self.user.get_full_name()

    def free_iphone_app_trial_expired(self, compare_date=datetime.today().date()):
        """
        Compare compare_date to iphone_free_use_date_start and checks if
        compare_date is more than 30 days older than iphone_free_use_date_start.
        If so we return True
        """
        if not self.iphone_free_use_date_start:
            return False
        else:
            return self.iphone_free_use_date_start < compare_date - timedelta(days=30)

    def get_space_balance_mb(self):
        """
        Return disk_space_balance balance in megabytes
        """
        return self.disk_space_balance / 1000 / 1000

    def recalc_disk_balance(self):
        """
        !! expensive BAD !!
        Go through each logbooks and logs and addup media file size.
        """
        total_size = 0
        for book in self.active_logbooks():
            for log in book.logs_qs():
                for f in log.files.all():
                    total_size += f.file.size

        self.disk_space_balance = total_size
        self.save()

    def can_upload_media(self):
        "Check if a user has enough space to upload media"
        if not self.has_payed_plan() and self.disk_space_balance > config.DISKSPACE_FREE_MAXMB * 1024 * 1024:
            return False
        return True

    def age(self, age=False):
        if not age:
            age = datetime.date.today()
        years = age.year - self.dob.year
        this_year_birthday = self.dob.replace(year=age.year)
        birthday_has_passed = age >= this_year_birthday
        if not birthday_has_passed:
            years = years - 1
        return years

    def is_noob(self, days=20):
        """
        Did the user joined less than <days> ago ?
        """
        if (timezone.now() - self.user.date_joined) < timedelta(days=days):
            return True
        return False

    def days_balance(self):
        """
        Returns the number of days left for a payed plan.
        We assume that one month is equal to 30 days
        """
        if self.plan == 1:
            return -1
        delta = timezone.now() - self.fplan_switch_date
        return delta.days

    def has_logbook_of_type(self, type_name):
        """
        Check if the user has a logbook of this type
        TODO
        """
        # raise NotImplementedError
        return False

    def logbooks(self, filters={}):
        """
        Return the list of log books owned by the user excluding deleted
        """
        return LogBookBase.existing_for_user(self.user.pk)

    def all_logbooks(self, filters={}):
        """
        Return the list of log books owned by the user including deleted
        """
        return LogBookBase.for_user(self.user.pk)

    def active_logbooks(self, raw=False, filters={}):
        """
        Do not include deleted and not visible logbooks
        """
        return LogBookBase.active_for_user(self.user.pk)

    # def consume_voucher(self, coupon_code):
    #     """
    #     Increment miles
    #     """
    #     user = self.user
    #     coupon = Coupon.objects.get_valid_or_none(coupon_code, user)
    #     if not coupon:
    #         return
    #     if coupon.reduc_type == "M":
    #         UserProfile.objects.filter(id=self.id).update(
    #             miles_balance=F("miles_balance") + coupon.discount_value
    #         )
    #     coupon.invalidate(self.user)

    def has_payed_plan(self):
        return self.plan == 2

    def generate_api_key(self):
        if not hasattr(self, "api_key"):
            return
        self.api_key = (
            base64.b64encode(
                hashlib.sha256(str(random.getrandbits(256)).encode()).digest(),
                random.choice([b"rA", b"aZ", b"gQ", b"hH", b"hG", b"aR", b"DD"]),
            )
            .decode()
            .rstrip("==")
        )
        self.save()


class ProfileSettings(models.Model):
    """
    Setting model for user
    It handles the 'alert by mail' choices for several notifications.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mail_on_notification = models.BooleanField(
        "Alertes",
        help_text="Recevoir les alertes (parrainage et événements) par email.",
        default=True,
    )

    def __str__(self):
        return f"{self.user}: {self.mail_on_notification}"


class Sponsorship(models.Model):
    sponsor = models.ForeignKey(User, related_name="nephews", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="sponsors", on_delete=models.CASCADE)
    created_date = models.DateField(auto_now_add=True)
    updated_date = models.DateField(auto_now=True)
    free_plan = models.BooleanField(default=False, help_text="Has the nephew signed up for a free account")
    payed_plan = models.BooleanField(default=False, help_text="Has the nephew signed up for a payed account")

    class Meta:
        verbose_name = "Sponsoring"
        verbose_name_plural = "Sponsorings"

    def __str__(self) -> str:
        return f"{self.sponsor.get_full_name()}, {self.user.get_full_name()}"

    @classmethod
    def generate_sponso_url_for(cls, user):
        h = hmac.new(settings.SECRET_KEY.encode(), str(user.id).encode(), hashlib.sha256)
        signature = base64.urlsafe_b64encode(h.digest()).decode()
        return f"?p={signature}&uid={user.id}"


# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         UserProfile.objects.create(user=instance)


# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     instance.userprofile.save()


def alert_managers(sender, **kwargs):
    if kwargs["created"] == True:
        plan = PLAN_CHOICES[kwargs["instance"].plan - 1]
        # real_log("notices", "New user subscribed to %s" % plan[1])
        # if config.MAIL_ON_SUBSCRIBE == True:
        #     from django.core.mail import mail_managers
        #     msg = "New user signed up!"
        #     title = "[%s] New subscription" % plan[1]
        #     mail_managers(title, msg, fail_silently=True)


post_save.connect(alert_managers, sender=UserProfile)


def clean_user_email(sender, instance, **kwargs):
    instance.email = instance.email.lower()


pre_save.connect(clean_user_email, sender=User)
