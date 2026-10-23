"""cloudy URL Configuration."""

from constance import config
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, register_converter
from django.urls.converters import SlugConverter
from django.views.generic import RedirectView, TemplateView

from cloudy.core import admin_views
from cloudy.core import views as core_views


class EmptyOrSlugConverter(SlugConverter):
    regex = "[-a-zA-Z0-9_]*"


register_converter(EmptyOrSlugConverter, "emptyorslug")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", core_views.home, name="home"),
    path("data/cgvu/", TemplateView.as_view(template_name="popups/data_cgvu.html"), name="cgvu"),
    path("gcu/", TemplateView.as_view(template_name="gcu.html"), name="gcu"),
    path("contactus/", TemplateView.as_view(template_name="contactus.html"), name="contactus"),
    path(
        "fly-green-aviation/",
        TemplateView.as_view(template_name="fly_green_aviation.html"),
        name="fly_green_aviation",
    ),
    path("features/", TemplateView.as_view(template_name="features.html"), name="features"),
    path("support/", TemplateView.as_view(template_name="support.html"), name="support"),
    path("connecteurs/", TemplateView.as_view(template_name="mcp_guide.html"), name="mcp_guide"),
    path(
        "pricing/",
        TemplateView.as_view(
            template_name="pricing.html",
            extra_context={"first_class_price": config.FIRST_CLASS_PRICE},
        ),
        name="pricing",
    ),
    path("logbooks/", include("cloudy.logbooks.urls")),
    path("accounts/", include("cloudy.accounts.urls")),
    path("faq/", include("cloudy.faq.urls")),
    path("ref/", include("cloudy.urlshortener.urls")),
    path("press/", include(("cloudy.press.urls", "press"), namespace="press")),
    path("payment/", include("cloudy.payment.urls")),
    path("alerts/", include("cloudy.alerts.urls")),
    path("notices/", TemplateView.as_view(template_name="support.html"), name="notices"),
    path("profile/", RedirectView.as_view(pattern_name="profile", permanent=False)),
    path("api/", TemplateView.as_view(template_name="support.html"), name="api_gone"),
    path("search/", RedirectView.as_view(url="/faq/", permanent=False), name="search"),
    path("zendesk/", TemplateView.as_view(template_name="support.html"), name="zendesk_gone"),
    path("coupons/", TemplateView.as_view(template_name="support.html"), name="coupons_gone"),
    path("graphs/", include("cloudy.stats.urls")),
    path(
        "air/<slug:aeronef>/",
        TemplateView.as_view(template_name="features.html"),
        name="air_landing",
    ),
    path(
        "partners/<slug:partner>/",
        TemplateView.as_view(template_name="features.html"),
        name="partners",
    ),
    path("admin/logbooks/<user_id>/", admin_views.logbook_admin, name="admin_user_logbooks"),
    path("admin/alerts/alert/<alert_id>/", admin_views.alerts_admin, name="admin_user_alerts"),
    path("admin/logbooks/<logbook_id>/del/", admin_views.logbook_delete, name="admin_logbook_delete"),
    path("admin/unknown_airports/", admin_views.unknown_airports, name="unknown_airports"),
]

if settings.DEBUG:
    urlpatterns = [
        path("__debug__/", include("debug_toolbar.urls")),
    ] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
