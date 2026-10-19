from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import models

User = get_user_model()


class NoticeType(models.Model):
    label = models.CharField(max_length=50)
    display = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    default = models.IntegerField(db_column="default")

    class Meta:
        db_table = "notification_noticetype"

    def __str__(self) -> str:
        return self.label


class NoticeSetting(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notice_type = models.ForeignKey(NoticeType, on_delete=models.CASCADE)
    medium = models.CharField(max_length=1, default="1")
    send = models.BooleanField(default=False)

    class Meta:
        db_table = "notification_noticesetting"
        unique_together = ("user", "notice_type", "medium")

    @classmethod
    def for_user(cls, user, notice_type, medium=1):
        setting, _ = cls.objects.get_or_create(
            user=user,
            notice_type=notice_type,
            medium=str(medium),
            defaults={"send": notice_type.default == medium},
        )
        return setting


class Notice(models.Model):
    recipient = models.ForeignKey(User, related_name="received_notices", on_delete=models.CASCADE)
    sender = models.ForeignKey(
        User, related_name="sent_notices", null=True, blank=True, on_delete=models.CASCADE
    )
    message = models.TextField()
    notice_type = models.ForeignKey(NoticeType, on_delete=models.CASCADE)
    added = models.DateTimeField(auto_now_add=True)
    unseen = models.BooleanField(default=True)
    archived = models.BooleanField(default=False)
    on_site = models.BooleanField(default=False)

    class Meta:
        db_table = "notification_notice"
        ordering = ["-added"]


class ObservedItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notice_type = models.ForeignKey(NoticeType, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    added = models.DateTimeField(auto_now_add=True)
    # NOT NULL in the production table, which django-notification used to record
    # which signal the observation was registered for.
    signal = models.TextField()

    class Meta:
        db_table = "notification_observeditem"


NOTICE_MEDIA_DEFAULTS = {
    "1": {"id": 1, "label": "Email", "default": True},
}
