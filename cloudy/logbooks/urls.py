from django.urls import path

from cloudy.aircrafts import views as aircrafts_views
from cloudy.logbooks import views as logbooks_views

app_name = "logbooks"

# urlpatterns = [
#     path("", logbooks_views.home, name="home"),
# ]

urlpatterns = [
    path("", logbooks_views.home, name="home"),
    path("logbook/", logbooks_views.add_log_book, name="addlogbook"),
    path("<emptyorslug:logbook_id>/", logbooks_views.home, name="logbook"),
    path("<emptyorslug:logbook_id>/totals/", logbooks_views.totals, name="totals"),
    path("<emptyorslug:logbook_id>/stats/", logbooks_views.stats, name="stats"),
    path("<emptyorslug:logbook_id>/log/", logbooks_views.add_log, name="add_log"),
    path("<emptyorslug:logbook_id>/aeronefs/", logbooks_views.create_aeronef, name="add_aeronef"),
    path("<emptyorslug:logbook_id>/report/", logbooks_views.report, name="report"),
    path("<emptyorslug:logbook_id>/parametres/", logbooks_views.parameters, name="parameters"),
    # both urls point to add_log
    path(
        "<emptyorslug:logbook_id>/log/<emptyorslug:log_id>/",
        logbooks_views.add_log,
        name="add_log",
    ),
    path(
        "<emptyorslug:logbook_id>/log/<emptyorslug:log_id>/del/",
        logbooks_views.del_log,
        name="del_log",
    ),
    path(
        "<emptyorslug:logbook_id>/log_edit/<emptyorslug:log_id>/",
        logbooks_views.add_log,
        name="edit_log",
    ),
    path(
        "<emptyorslug:logbook_id>/export/<emptyorslug:ex_type>/",
        logbooks_views.export,
        name="export",
    ),
    #    path(r'<logbook_id>/import/$', 'upload_for_import', name='upload_for_import'),
    path("<emptyorslug:logbook_id>/import/", logbooks_views.import_home, name="import_home"),
    path("<emptyorslug:logbook_id>/import/auto/", logbooks_views.import_auto, name="auto_import"),
    path(
        "<emptyorslug:logbook_id>/import/processing/",
        logbooks_views.import_processing,
        name="import_processing",
    ),
]

urlpatterns += [
    path(
        "<logbook_id>/add_log_autocomplete/",
        aircrafts_views.add_log_autocomplete,
        name="add_log_autocomplete",
    ),
    path("<logbook_id>/aircrafts/", aircrafts_views.index, name="aircrafts_index"),
    path(
        "<logbook_id>/aircrafts/form/",
        aircrafts_views.form,
        {"aircraft_id": None},
        name="aircrafts_form",
    ),
    path(
        "<logbook_id>/aircrafts/form/airport_autocomplete/",
        aircrafts_views.airport_autocomplete,
        name="airport_autocomplete",
    ),
    path("<logbook_id>/aircrafts/form/<int:aircraft_id>/", aircrafts_views.form, name="aircrafts_form"),
    path(
        "<logbook_id>/aircrafts/delete/<aircraft_id>/",
        aircrafts_views.delete,
        name="aircrafts_delete",
    ),
]
