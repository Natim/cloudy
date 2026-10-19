from django.urls import path

from . import views

urlpatterns = [
    # path(r"^(?P<b36hash_code>[\w]+)/$", views.expand_url, name="expand"),   # DELETE
    path("<b36hash_code>", views.expand_url, name="expand"),
]
