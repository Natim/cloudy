from django.core.mail import mail_admins
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string

from cloudy.core.models import FileModel
from cloudy.core.signals import hard_error


@receiver(hard_error, dispatch_uid="hard_error")
def mail_error(sender, **kwargs):
    """Send an email to admins.
    TODO: We should use Django 1.3 built-in logger"""
    body_text = render_to_string(
        "mails/error_body.txt",
        {
            "msg": kwargs["msg"],
            "sender": sender,
        },
    )
    subject = "Payment Error: %s" % (kwargs["ctx"])
    mail_admins(subject.strip(), body_text, fail_silently=False)


@receiver(post_save, sender=FileModel)
def update_storage_balance(sender, instance, **kwargs):
    """
    Update the user disk balance each time he saves a filemodel, which means
    each time he upload or mark a file as deleted.
    """

    user = instance.owner
    user_files = FileModel.objects.filter(owner=user, deleted=False)
    user_profile = user.userprofile

    used = sum(fo.file.size for fo in user_files)
    user_profile.disk_space_balance = used
    user_profile.save()
