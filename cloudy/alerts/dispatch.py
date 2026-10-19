"""
Alerts dispatchers - email only.
"""

from django.conf import settings
from django.core.mail import send_mail
from django.template import loader

from cloudy.alerts.models import QualificationGlissante


def sms(qualification, draft=False, **kwargs):
    """SMS alerts disabled; use email dispatch instead."""
    return email(qualification, draft=draft, **kwargs)


def email(qualification, draft=False, **kwargs):
    user = qualification.ownr
    email_addr = user.email

    if isinstance(qualification, QualificationGlissante):
        if kwargs.get("recursive") is True:
            template = "mails/alerts/recursive_slippery_alert.html"
        else:
            template = "mails/alerts/slippery_alert.html"
        context = {
            "qualification": qualification,
            "delta": kwargs["delta"],
            "user": user,
        }
    else:
        template = "mails/alerts/alert.html"
        context = {
            "qualification": qualification,
            "alert": kwargs["alert"],
            "delta": kwargs["delta"],
            "user": user,
            "name": kwargs["name"],
        }

    body = loader.render_to_string(template, context)
    title = loader.render_to_string("mails/alerts/alert_title.html", context).strip()
    if not draft:
        send_mail(
            title,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [email_addr],
            fail_silently=False,
        )
