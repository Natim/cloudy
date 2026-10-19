import logging

import stripe
from constance import config
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from cloudy.accounts.models import UserProfile
from cloudy.core.utils import render_to
from cloudy.notifications import services as notification
from cloudy.payment.models import ProcessedStripeEvent
from cloudy.payment.signals import upgrade_plan_complete

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_API_KEY


@login_required
def cloudy_pack(request):
    return render(
        request,
        "payment/pcloudy.html",
        {"STRIPE_FIRST_CLASS_SUBSCRIPTION": settings.STRIPE_FIRST_CLASS_SUBSCRIPTION},
    )


@require_POST
@login_required
def create_checkout_session(request):
    price_id = settings.STRIPE_FIRST_CLASS_SUBSCRIPTION
    if not price_id:
        return JsonResponse(
            {"error": {"message": "First Class subscription is not configured."}},
            status=500,
        )

    try:
        checkout_session = stripe.checkout.Session.create(
            success_url=request.build_absolute_uri("/payment/pack/payed/?session_id={CHECKOUT_SESSION_ID}"),
            cancel_url=request.build_absolute_uri("/payment/pack/closed/"),
            payment_method_types=["card"],
            customer_email=request.user.email,
            client_reference_id=str(request.user.id),
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
        )
        return JsonResponse({"sessionId": checkout_session.id})
    except Exception:
        logger.exception("Stripe checkout session creation failed")
        return JsonResponse(
            {"error": {"message": "Unable to start checkout. Please try again later."}},
            status=400,
        )


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError, stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if isinstance(event, dict):
        event_id = event["id"]
        event_type = event["type"]
        data_object = event["data"]["object"]
    else:
        event_id = event.id
        event_type = event.type
        data_object = event.data.object

    if ProcessedStripeEvent.objects.filter(event_id=event_id).exists():
        return HttpResponse(status=200)

    try:
        with transaction.atomic():
            if event_type == "checkout.session.completed":
                _handle_checkout_completed(data_object)
            elif event_type == "invoice.paid":
                _handle_invoice_paid(data_object)
            elif event_type == "customer.subscription.deleted":
                _handle_subscription_deleted(data_object)
            ProcessedStripeEvent.objects.create(event_id=event_id, event_type=event_type)
    except IntegrityError:
        return HttpResponse(status=200)
    except Exception:
        logger.exception("Stripe webhook handler failed for event %s", event_id)
        return HttpResponse(status=500)

    return HttpResponse(status=200)


def _activate_first_class(profile: UserProfile, user) -> None:
    profile.plan = 2
    profile.fplan_switch_date = timezone.now()
    profile.month_balance = 12
    if config.BETA:
        profile.month_balance += config.BETA_MONTH_BONUS
    profile.save()
    upgrade_plan_complete.send(sender=profile, user=user)
    notification.send([user], "fistclass_payed", {"user": user})


def _session_has_first_class_price(session: dict) -> bool:
    expected = settings.STRIPE_FIRST_CLASS_SUBSCRIPTION
    if not expected:
        logger.warning("STRIPE_FIRST_CLASS_SUBSCRIPTION not configured")
        return False

    session_id = session.get("id")
    if not session_id:
        return False

    try:
        line_items = stripe.checkout.Session.list_line_items(session_id, limit=10)
    except stripe.error.StripeError:
        logger.exception("Failed to list checkout session line items for %s", session_id)
        return False

    for item in line_items.data:
        price = item.price
        price_id = price.id if hasattr(price, "id") else price.get("id")
        if price_id == expected:
            return True
    return False


def _price_id_from_line(line: dict) -> str | None:
    price = line.get("price")
    if price is None:
        return None
    if isinstance(price, str):
        return price
    if isinstance(price, dict):
        return price.get("id")
    return getattr(price, "id", None)


def _invoice_has_first_class_price(invoice: dict) -> bool:
    expected = settings.STRIPE_FIRST_CLASS_SUBSCRIPTION
    if not expected:
        logger.warning("STRIPE_FIRST_CLASS_SUBSCRIPTION not configured")
        return False
    lines = invoice.get("lines") or {}
    if hasattr(lines, "get"):
        line_items = lines.get("data", [])
    else:
        line_items = getattr(lines, "data", [])
    for line in line_items:
        price_id = _price_id_from_line(line if isinstance(line, dict) else line)
        if price_id == expected:
            return True
    return False


def _handle_checkout_completed(session: dict) -> None:
    user_id = session.get("client_reference_id")
    if not user_id:
        return
    from django.contrib.auth.models import User

    try:
        user = User.objects.get(pk=int(user_id))
    except User.DoesNotExist, ValueError:
        return

    if not _session_has_first_class_price(session):
        logger.warning(
            "Checkout session %s did not pay for configured First Class price",
            session.get("id"),
        )
        return

    profile = user.userprofile
    update_fields = []
    if session.get("customer"):
        profile.stripe_customer_id = session["customer"]
        update_fields.append("stripe_customer_id")
    if session.get("subscription"):
        profile.stripe_subscription_id = session["subscription"]
        update_fields.append("stripe_subscription_id")
    if update_fields:
        profile.save(update_fields=update_fields)

    if session.get("payment_status") != "paid":
        logger.warning(
            "Skipping First Class activation for checkout.session.completed with payment_status=%s",
            session.get("payment_status"),
        )
        return
    _activate_first_class(profile, user)


def _handle_invoice_paid(invoice: dict) -> None:
    customer_id = invoice.get("customer")
    if not customer_id:
        return
    try:
        profile = UserProfile.objects.get(stripe_customer_id=customer_id)
    except UserProfile.DoesNotExist:
        return
    if not _invoice_has_first_class_price(invoice):
        return

    user = profile.user
    if profile.plan != 2:
        _activate_first_class(profile, user)
        return

    profile.fplan_switch_date = timezone.now()
    profile.save(update_fields=["fplan_switch_date"])


def _handle_subscription_deleted(subscription: dict) -> None:
    customer_id = subscription.get("customer")
    if not customer_id:
        return
    try:
        profile = UserProfile.objects.get(stripe_customer_id=customer_id)
    except UserProfile.DoesNotExist:
        return
    profile.plan = 1
    profile.stripe_subscription_id = ""
    profile.save(update_fields=["plan", "stripe_subscription_id"])


@render_to("registration/registration_complete_payed.html")
def register_complete_payed(request):
    return {}


@render_to("registration/registration_closed.html")
def register_closed(request):
    return {}
