from unittest import mock

import stripe
from django.contrib.auth.models import User
from django.test import Client, override_settings, TestCase

from cloudy.api.auth import issue_access_token

CHECKOUT_URL = "https://checkout.stripe.com/c/pay/cs_test"


def bearer(user: User) -> dict[str, str]:
    token, _expires = issue_access_token(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@override_settings(STRIPE_API_KEY="sk_test_x", STRIPE_FIRST_CLASS_SUBSCRIPTION="price_first_class")
class StripeCheckoutTests(TestCase):
    fixtures = ["testing_data.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(email="simple@example.com")
        self.headers = bearer(self.user)

    def checkout(self, **headers):
        return self.client.post("/api/v1/payment/stripe/checkout", **headers)

    def test_rejects_anonymous_callers(self):
        self.assertEqual(self.checkout().status_code, 401)

    @override_settings(STRIPE_FIRST_CLASS_SUBSCRIPTION="")
    def test_unconfigured_price_is_reported(self):
        resp = self.checkout(**self.headers)
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.json()["code"], "checkout_unconfigured")

    @mock.patch("cloudy.api.routes.payments.stripe.checkout.Session.create")
    @mock.patch("cloudy.api.routes.payments.stripe.Price.retrieve")
    def test_opens_a_subscription_session_for_the_caller(self, retrieve, create):
        retrieve.return_value = mock.Mock(recurring={"interval": "year"})
        create.return_value = mock.Mock(id="cs_test", url=CHECKOUT_URL)

        resp = self.checkout(**self.headers)
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.json(), {"url": CHECKOUT_URL})

        params = create.call_args.kwargs
        self.assertEqual(params["client_reference_id"], str(self.user.pk))
        self.assertEqual(params["mode"], "subscription")
        self.assertEqual(params["customer_email"], "simple@example.com")
        self.assertEqual(params["line_items"], [{"price": "price_first_class", "quantity": 1}])
        self.assertTrue(
            params["success_url"].endswith("/payment/pack/payed/?session_id={CHECKOUT_SESSION_ID}")
        )
        self.assertTrue(params["cancel_url"].endswith("/payment/pack/closed/"))

    @mock.patch(
        "cloudy.api.routes.payments.stripe.Price.retrieve",
        side_effect=stripe.APIConnectionError("down"),
    )
    def test_stripe_failure_is_reported(self, _retrieve):
        resp = self.checkout(**self.headers)
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.json()["code"], "checkout_failed")
