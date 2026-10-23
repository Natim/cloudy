from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from cloudy.notifications.models import Notice, NoticeSetting, NoticeType


def create_notice_type(label: str, display: str, description: str, default: int = 2) -> NoticeType:
    notice_type, _ = NoticeType.objects.get_or_create(
        label=label,
        defaults={"display": display, "description": description, "default": default},
    )
    return notice_type


def send(users, notice_type_label: str, extra_context: dict | None = None) -> None:
    extra_context = extra_context or {}
    if notice_type_label in getattr(settings, "NOTICE_TYPE_IGNORE", []):
        return

    try:
        notice_type = NoticeType.objects.get(label=notice_type_label)
    except NoticeType.DoesNotExist:
        return

    for user in users:
        Notice.objects.create(
            recipient=user,
            sender=None,
            notice_type=notice_type,
            message=notice_type.description,
        )
        setting = NoticeSetting.for_user(user, notice_type, medium=1)
        if not setting.send:
            continue
        subject = render_to_string(
            f"notification/{notice_type_label}/short.txt",
            extra_context,
            using=None,
        ).strip()
        body = render_to_string(
            f"notification/{notice_type_label}/full.txt",
            extra_context,
            using=None,
        )
        send_mail(
            subject or notice_type.display,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
