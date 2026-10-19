from django.urls import path
from django.views.generic import ListView

from .models import Article

urlpatterns = [
    path("", ListView.as_view(model=Article, template_name="press/press.html"), name="list"),
]
