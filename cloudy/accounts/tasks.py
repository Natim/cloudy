from datetime import datetime

from django.conf import settings
from django.db import transaction
from django.db.models.signals import pre_save
from django_registration.signals import user_registered

from cloudy.accounts.models import UserProfile
from cloudy.logbooks.models import LogBookBase
from cloudy.notifications.models import NoticeSetting, NoticeType


# @transaction.commit_on_success()
@transaction.atomic()
def finish_registration(sender, user, **kwargs):
    """
    Registration signal
    - Ensure profile exists (created by CloudyRegistrationView for web signup)
    - Apply legacy register_kwargs when provided
    - Set notice settings
    """
    payment_order = kwargs.get("payment_order", None)
    register_kwargs = kwargs.get("register_kwargs")

    if register_kwargs is not None:
        user.first_name = register_kwargs["first_name"]
        user.last_name = register_kwargs["last_name"]
        user.save(update_fields=["first_name", "last_name"])
        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={"dob": register_kwargs["dob"]},
        )
        profile.dob = register_kwargs["dob"]
        profile.generate_api_key()
        if payment_order:
            profile.plan = 2
            profile.month_balance = 12
            profile.fplan_switch_date = datetime.now()
        profile.save()
    elif not UserProfile.objects.filter(user=user).exists():
        return None

    if payment_order:
        payment_order.user = user
        payment_order.save()

    types = NoticeType.objects.all()
    for notice_type in types:
        if notice_type.label in settings.NOTICE_TYPE_IGNORE:
            notice_setting = NoticeSetting.for_user(user, notice_type, 0)
            notice_setting.send = False
            notice_setting.save()


user_registered.connect(finish_registration, dispatch_uid="cloudy.accounts.models")


def pack_change_handler(sender, **kwargs):
    """
    If a pack was in paid mode and is going to move to eco we
    disable (delete=true) all logbooks but the first for this user.
    """
    user_profile = kwargs["instance"]
    try:
        current_profile = UserProfile.objects.get(id=user_profile.id)
    except UserProfile.DoesNotExist:
        # First create, no need to continue we are certain he has no logbooks
        return

    old_plan_value = current_profile.plan
    new_plan_value = kwargs["instance"].plan

    # if moving from first to eco we hide extra logbooks (1 max)
    logbooks = LogBookBase.existing_for_user(user_profile.user)
    if old_plan_value == 2 and new_plan_value == 1:
        for logbook in logbooks[1:]:
            logbook.visbl = False
            logbook.save()

    if old_plan_value == 1 and new_plan_value == 2:
        for logbook in logbooks:
            logbook.visbl = True
            logbook.save()


pre_save.connect(pack_change_handler, sender=UserProfile, dispatch_uid="cloudy.accounts.profile")
