"""Six-digit codes mailed for mobile sign-up and password reset."""

import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from cloudy.accounts.models import EmailCode

from .errors import ApiHttpError

CODE_TTL = timedelta(minutes=10)
RESEND_COOLDOWN = timedelta(seconds=60)
MAX_ATTEMPTS = 5


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _hash(code: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), code.encode(), hashlib.sha256).hexdigest()


def otp_invalid() -> ApiHttpError:
    return ApiHttpError(400, "Invalid code", code="OTP_INVALID")


def otp_expired() -> ApiHttpError:
    return ApiHttpError(400, "Expired code", code="OTP_EXPIRED")


def recently_sent(email: str, purpose: str) -> bool:
    since = timezone.now() - RESEND_COOLDOWN
    return EmailCode.objects.filter(email=email, purpose=purpose, created_at__gt=since).exists()


def issue_code(email: str, purpose: str) -> str:
    """Replace any pending code for this address and purpose, then mail a new one."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    with transaction.atomic():
        EmailCode.objects.filter(email=email, purpose=purpose, used_at__isnull=True).delete()
        EmailCode.objects.create(
            email=email,
            purpose=purpose,
            code_hash=_hash(code),
            expires_at=timezone.now() + CODE_TTL,
        )
    context = {"code": code, "minutes": int(CODE_TTL.total_seconds() // 60), "purpose": purpose}
    subject = render_to_string("accounts/email_code_subject.txt", context).strip()
    subject = settings.EMAIL_SUBJECT_PREFIX + subject
    body = render_to_string("accounts/email_code_body.txt", context)
    html = render_to_string("accounts/email_code_body.html", {**context, "subject": subject})
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email], html_message=html)
    return code


def check_code(email: str, code: str, purposes: tuple[str, ...]) -> EmailCode:
    """Return the pending code row matching ``code``, or raise OTP_INVALID / OTP_EXPIRED.

    A wrong guess counts against the latest code; after MAX_ATTEMPTS it is burnt.
    """
    submitted = _hash((code or "").strip())
    now = timezone.now()
    with transaction.atomic():
        rows = EmailCode.objects.select_for_update().filter(
            email=email, purpose__in=purposes, used_at__isnull=True
        )
        live = [
            row
            for row in rows.order_by("-created_at")
            if row.expires_at > now and row.attempts < MAX_ATTEMPTS
        ]
        for row in live:
            if hmac.compare_digest(row.code_hash, submitted):
                return row
        if not live:
            error = otp_expired()
        else:
            latest = live[0]
            latest.attempts += 1
            latest.save(update_fields=["attempts"])
            error = otp_expired() if latest.attempts >= MAX_ATTEMPTS else otp_invalid()
    # Raised outside the atomic block so the attempt counter is kept.
    raise error


def consume(row: EmailCode) -> None:
    row.used_at = timezone.now()
    row.save(update_fields=["used_at"])
