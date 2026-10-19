from django.urls import path

from . import views

app_name = "alerts"

urlpatterns = [
    path(
        "qualifications/",
        views.qualification,
        {"uid": None, "qtype": "qualification"},
        name="qualification",
    ),
    path(
        "qualifications/<int:uid>/",
        views.qualification,
        {"qtype": "qualification"},
        name="qualification_detail",
    ),
    path("medicals/", views.qualification, {"uid": None, "qtype": "medical"}, name="medical"),
    path(
        "medicals/<int:uid>/",
        views.qualification,
        {"qtype": "medical"},
        name="medical_detail",
    ),
    path("glide/", views.glide, {"uid": None, "qtype": "glide"}, name="glide"),
    path("glide/<int:uid>/", views.glide, {"qtype": "glide"}, name="glide_detail"),
    path(
        "medicals/delete/<int:uid>/",
        views.delete,
        {"qtype": "medical"},
        name="delete_medical",
    ),
    path(
        "qualifications/delete/<int:uid>/",
        views.delete,
        {"qtype": "qualification"},
        name="delete_qualification",
    ),
    path("glide/delete/<int:uid>/", views.delete, {"qtype": "glide"}, name="delete_glide"),
    path("data/sub_type/", views.get_subtype, name="ajax_subtype"),
    path("data/type/", views.get_type, name="ajax_type"),
    path("data/qualifications_list/", views.get_qualifications_list, name="ajax_qualifications_list"),
    path("data/qualification/", views.get_qualification, name="ajax_qualification"),
    path("data/medicals/", views.get_medicals_list, name="ajax_medicals"),
    path("data/glides_list/", views.get_glides_list, name="ajax_glides_list"),
]
