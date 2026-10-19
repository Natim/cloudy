from django.urls import path

from . import views

app_name = "payment"

urlpatterns = [
    path("pack/", views.cloudy_pack, name="pcloudy"),
    path("pack/payed/", views.register_complete_payed, name="pack_payed"),
    path("pack/closed/", views.register_closed, name="pack_closed"),
    path(
        "create_checkout_settings/",
        views.create_checkout_session,
        name="create_checkout_session",
    ),
    path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
]
