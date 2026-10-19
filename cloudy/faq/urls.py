from django.urls import path
from django.views.generic import DetailView, ListView

from .models import Faq

app_name = "faq"
urlpatterns = [
    path("", ListView.as_view(model=Faq, template_name="faq/list.html"), name="list"),
    path("<pk>", DetailView.as_view(model=Faq, template_name="faq/details.html"), name="details"),
]
