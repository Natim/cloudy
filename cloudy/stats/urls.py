from django.urls import path

from . import views

app_name = "stats"
urlpatterns = [
    path("data/", views.graphs_data, name="graphs_data"),
    path("count_airports/", views.airports, name="airports"),
    path("count_foo/", views.count_foo, name="count_foo"),
    path("get_choices/", views.get_choices, name="get_choices"),
    path("map/", views.map_places, name="map_places"),
]
