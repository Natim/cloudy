import logging

import stripe
from django.conf import settings
from django.http import HttpRequest
from ninja import Router

from cloudy.payment.views import _checkout_return_url

from ..auth import require_user
from ..errors import ApiHttpError
from ..schemas.payments import CheckoutOut
from ._common import bearer_auth

logger = logging.getLogger(__name__)

router = Router(tags=["payment"])

# Same return pages as the website checkout: the app watches for the paid one.
PAID_PATH = "/payment/pack/payed/?session_id={CHECKOUT_SESSION_ID}"
CLOSED_PATH = "/payment/pack/closed/"


def _checkout_failed() -> ApiHttpError:
    return ApiHttpError(503, "The payment could not be started", code="checkout_failed")


@router.post("/payment/stripe/checkout", response=CheckoutOut, auth=bearer_auth)
def create_stripe_checkout(request: HttpRequest):
    """Open a Stripe Checkout session for First Class and return its URL.

    The app opens the URL in the phone's browser. The plan is granted by the
    checkout.session.completed webhook, as for a payment started on the website.
    """
    user = require_user(request)
    price_id = (settings.STRIPE_FIRST_CLASS_SUBSCRIPTION or "").strip()
    if not price_id or not settings.STRIPE_API_KEY:
        logger.error("Stripe checkout is not configured")
        raise ApiHttpError(503, "First Class checkout is not configured", code="checkout_unconfigured")

    try:
        price = stripe.Price.retrieve(price_id, api_key=settings.STRIPE_API_KEY)
        params = {
            "success_url": _checkout_return_url(request, PAID_PATH),
            "cancel_url": _checkout_return_url(request, CLOSED_PATH),
            # The webhook finds the account with this id.
            "client_reference_id": str(user.id),
            "mode": "subscription" if price.recurring else "payment",
            "line_items": [{"price": price_id, "quantity": 1}],
        }
        if user.email:
            params["customer_email"] = user.email
        session = stripe.checkout.Session.create(api_key=settings.STRIPE_API_KEY, **params)
    except stripe.StripeError as exc:
        logger.exception("Stripe checkout session creation failed for user %s", user.pk)
        raise _checkout_failed() from exc

    if not session.url:
        logger.error("Stripe checkout session %s has no redirect url", session.id)
        raise _checkout_failed()
    return {"url": session.url}
