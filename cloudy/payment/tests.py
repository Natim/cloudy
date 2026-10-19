import uuid
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from cloudy.accounts.models import UserProfile
from cloudy.payment.models import PaymentOrder, ProcessedStripeEvent
from cloudy.payment.views import _handle_checkout_completed


class PaymentOrderTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("paytest", "pay@test.com", "secret")
        self.order = PaymentOrder.objects.create(
            uuid=str(uuid.uuid4()),
            user=self.user,
            state=3,
            amount=12000,
        )

    def test_order_str(self):
        self.assertIn("120", str(self.order))

    def test_processed_stripe_event_unique(self):
        ProcessedStripeEvent.objects.create(event_id="evt_1", event_type="checkout.session.completed")
        with self.assertRaises(Exception):
            ProcessedStripeEvent.objects.create(event_id="evt_1", event_type="checkout.session.completed")


@override_settings(
    STRIPE_FIRST_CLASS_SUBSCRIPTION="price_first_class",
    STRIPE_API_KEY="sk_test",
)
class StripeCheckoutSecurityTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("paytest", "pay@test.com", "secret")
        UserProfile.objects.create(user=self.user, dob="1990-01-01")
        self.client = Client()
        self.client.login(username="paytest", password="secret")

    @patch("cloudy.payment.views.stripe.checkout.Session.create")
    def test_checkout_ignores_client_price_id(self, mock_create):
        mock_create.return_value = MagicMock(id="cs_test")
        response = self.client.post(
            reverse("payment:create_checkout_session"),
            data='{"priceId": "price_cheap"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        mock_create.assert_called_once()
        self.assertEqual(
            mock_create.call_args.kwargs["line_items"],
            [{"price": "price_first_class", "quantity": 1}],
        )

    @override_settings(STRIPE_FIRST_CLASS_SUBSCRIPTION="")
    def test_checkout_fails_when_price_not_configured(self):
        response = self.client.post(
            reverse("payment:create_checkout_session"),
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 500)

    @patch("cloudy.payment.views.stripe.checkout.Session.list_line_items")
    def test_webhook_skips_wrong_price(self, mock_list):
        mock_list.return_value = MagicMock(data=[MagicMock(price=MagicMock(id="price_cheap"))])
        session = {
            "id": "cs_test",
            "client_reference_id": str(self.user.id),
            "customer": "cus_x",
            "subscription": "sub_x",
        }
        _handle_checkout_completed(session)
        self.user.userprofile.refresh_from_db()
        self.assertEqual(self.user.userprofile.plan, 1)

    @patch("cloudy.payment.views.stripe.checkout.Session.list_line_items")
    @patch("cloudy.payment.views._activate_first_class")
    def test_checkout_skips_unpaid_status(self, mock_activate, mock_list):
        mock_list.return_value = MagicMock(data=[MagicMock(price=MagicMock(id="price_first_class"))])
        session = {
            "id": "cs_test",
            "client_reference_id": str(self.user.id),
            "payment_status": "unpaid",
        }
        _handle_checkout_completed(session)
        mock_activate.assert_not_called()

    @patch("cloudy.payment.views.stripe.checkout.Session.list_line_items")
    @patch("cloudy.payment.views._activate_first_class")
    def test_webhook_activates_for_configured_price(self, mock_activate, mock_list):
        mock_list.return_value = MagicMock(data=[MagicMock(price=MagicMock(id="price_first_class"))])
        session = {
            "id": "cs_test",
            "client_reference_id": str(self.user.id),
            "customer": "cus_x",
            "subscription": "sub_x",
            "payment_status": "paid",
        }
        _handle_checkout_completed(session)
        mock_activate.assert_called_once()
