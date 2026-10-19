# Django imports {{{
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse

# }}}
# Cloudy {{{
from cloudy.logbooks.models import LogBookBase

# }}}


IMPORT_STATES = (
    (1, "To be assigned"),
    (2, "In progress"),
    (3, "Awaiting information"),
    (4, "Done"),
    (5, "Rejected"),
)

LOGBOOK_STATES = (
    (0, "Nothing done"),
    (1, "Converted"),
    (2, "Imported"),
    (3, "Tested"),
)


class Import(models.Model):
    owner = models.ForeignKey(
        User,
        limit_choices_to={"is_staff": True},
        related_name="owned_imports",
        on_delete=models.CASCADE,
    )
    import_state = models.IntegerField(choices=IMPORT_STATES)
    logbook_state = models.IntegerField(choices=LOGBOOK_STATES)
    user = models.ForeignKey(User, related_name="imports_status", on_delete=models.CASCADE)
    logbook = models.ForeignKey(LogBookBase, on_delete=models.CASCADE)
    comments = models.TextField(blank=True, null=True)
    send_notification = models.BooleanField(
        help_text="Will send an email if the import goes successfully.", default=True
    )
    notification_delivered = models.BooleanField(default=False)

    minutes_only = models.BooleanField(
        default=True,
        help_text="If checked, the import algorithm will treat time\
                    cells as integers, representing a minute number.",
    )

    file_name = models.CharField(max_length=200, default="")

    cdate = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True, db_column="udate")

    original_file = models.FileField(
        upload_to="original_csv/",
        blank=True,
        null=True,
        help_text="This is the original file, submitted by the user.",
    )

    def type(self):
        return self.logbook.cat

    def get_absolute_url(self):
        url = reverse("admin:index")
        return "https://cloudy.fr" + url + "imports/imports/" + str(self.pk) + "/"


def _notify_mail(instance):
    owner = instance.owner

    # This URL reverse is definitely utterly ugly and prone to fail.
    # TODO rewrite this shit.
    body_html = render_to_string(
        "mails/import/notify_owner.html",
        {"full_name": owner.get_full_name(), "url": instance.get_absolute_url()},
    )

    subject = render_to_string("mails/import/notify_owner_subject.html", {})
    subject = subject.replace("\n", "")

    send_mail(subject, body_html, "no-reply@cloudy.fr", [owner.email])


@receiver(pre_save, sender=Import, dispatch_uid="cloudy.imports.models")
def notify_manager_assignment(sender, instance, **kwargs):
    if instance.pk == None:
        return True

    old = sender.objects.get(pk=instance.pk)
    if old.owner == instance.owner:  # Owner haven't changed.
        return True

    _notify_mail(instance)


@receiver(post_save, sender=Import, dispatch_uid="cloudy.imports.models")
def notify_manager_create(sender, instance, created, **kwargs):
    if not created:
        return True
    _notify_mail(instance)
