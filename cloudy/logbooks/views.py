# System imports {{{
import pathlib
import tempfile
import time
from datetime import datetime, timedelta
from os import path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.core.files.base import ContentFile
from django.forms.utils import ErrorList

# }}}
# Django imports {{{
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.template import defaultfilters
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone as django_timezone
from django.views.decorators.http import require_POST

from cloudy.core.models import FileModel

# from cloudy.accounts.decorators import user_has_plan  # TODO
from cloudy.core.utils import convert_str_to_date, is_ajax
from cloudy.height_format import HEIGHT_FORMAT_CHOICES
from cloudy.logbooks import paginator
from cloudy.logbooks import settings as book_settings
from cloudy.logbooks.decorators import fetch_logbook, fetch_range_select

# }}}
# Cloudy {{{
from cloudy.logbooks.forms import (
    AutoImportForm,
    DeleteLbookForm,
    EditLbookNameForm,
    FileCommentsForm,
)
from cloudy.logbooks.icao import icao_from_place
from cloudy.logbooks.models import LogBase, LogBookBase

# }}}
# Third-party apps {{{
from cloudy.notifications import services as notification
from cloudy.time_format import TIME_FORMAT_CHOICES
from cloudy.utils import json_fail, json_ok

LIVE_EDIT_FORBIDDEN_FIELDS = frozenset(
    {
        "id",
        "pk",
        "lbook",
        "lbook_id",
        "content_type",
        "content_type_id",
        "deleted",
        "visbl",
        "cdate",
        "update",
        "files",
    }
)


def _live_edit_field_allowed(log, field_name):
    if field_name in LIVE_EDIT_FORBIDDEN_FIELDS or "." in field_name:
        return False
    try:
        log._meta.get_field(field_name)
    except FieldDoesNotExist:
        return False
    return True


# }}}

# Data {{{
MB = 1024 * 1024
# }}}
END_DAY_TIME = {"hour": 23, "minute": 59, "second": 59, "microsecond": 999999}


@login_required
@fetch_logbook
def home(request, logbook_id=None, page_nbr=None, template="logbooks/home", extra_context={}):
    """
    Logbooks home
    """

    # We grab the page number. If the user has not provided one, we set to -1
    # in order to adapt paging computation.
    if not page_nbr:
        page = int(request.GET.get("p", -1))
    else:
        page = int(page_nbr)

    # Bind some variables for readability.
    logbook = request.logbook
    logbooks = request.logbooks

    # If the user does not have any logbook, we display a special page.
    if logbook is None:
        template = "logbooks/home_none.html"
        return render(request, template_name=template, context={"logbooks": logbooks})

    # Otherwise we load the appropriate template for the selected logbook.
    template = f"{template}_{logbook.cat}.html"

    # Get max rows for this model

    maxrows = logbook.rows_per_page()

    # Grab the number of pages and the logs to display on the current page.
    try:
        pages_count, logs_for_page = paginator.logs_for_page(logbook, page, maxrows=maxrows)
    except IndexError:
        pages_count, logs_for_page = paginator.logs_for_page(logbook, -1, maxrows=maxrows)

    # Check if the logbook is empty.
    # The idea is: if there is no log to display on the current page, either
    # the paginator bugs, or there is no log at all in the logbook. We assume
    # it is the second option.
    is_empty = False
    number_of_logs = len(logs_for_page)
    if number_of_logs == 0:
        is_empty = True

    # We want to display an alert message if its logbook is empty.
    if is_empty:
        # This message should be displayed only during the first two months
        # after the user created its logbook.
        cdate = logbook.cdate
        if django_timezone.is_naive(cdate):
            cdate = django_timezone.make_aware(cdate)
        if (django_timezone.now() - cdate) < timedelta(days=2 * 31):
            notification.send([request.user], "empty_logbook", {"logbook": logbook})

    # Go to the last page if the page number is -1
    if page == -1:
        page = pages_count

    # Now we grab the totals for this page
    totals_dict = {}
    if number_of_logs > 0:
        end_date = logs_for_page[0].date - timedelta(microseconds=1)
        totals_dict = logbook.get_totals(
            logbook.home_page_totals(), time_slice=(None, end_date), reports=True
        )
        # Get the first log position
        first_log_for_page = logs_for_page[0]
        # count the number of earlier logs
        filters = {
            "date__lte": first_log_for_page.date,
            "lbook": logbook,
            "deleted": False,
            "visbl": True,
        }
        earlier_logs_count = logbook._log_model().objects.filter(**filters).count()
        # Add the number of reported n number of logs from report 'start_count'
        if "jump_count" in logbook.reports:
            earlier_logs_count += int(logbook.reports["jump_count"])
        # Add a position parameter to each logs on this page
        for log in logs_for_page:
            log.position = earlier_logs_count
            earlier_logs_count += 1

    # else we have no logs but may still have totals from report
    # to show
    else:
        totals_dict = logbook.get_totals(logbook.home_page_totals(), time_slice=(None, None), reports=True)
    # Finally, render the template
    context = {
        "logbooks": logbooks,
        "logbook": logbook,
        "pages_count": pages_count,
        "page": page,
        "logs": logs_for_page,
        "is_empty": is_empty,
        "maxrows": maxrows,
        "iteration": range(0, maxrows),
        "totals": totals_dict,
        "LogModel": logbook._log_model(),
    }

    # Take into account eventual additional data in the context
    context.update(extra_context)

    # Render!
    return render(request, template, context)


@login_required
@require_POST
def add_log_book(request):
    """
    Create a new logbook instance
    This method is called from add_logbook.html popup
    """
    # We validate the form here (TODO: nice form as usual)
    logbooktypes = []
    for item in request.POST:
        if item in settings.LOG_BOOKS_TYPE and request.POST[item] == "1":
            logbooktypes.append(item)

    # Want to create more then on logbook and is in free plan ? -> error
    if (
        not request.user.userprofile.has_payed_plan()
        and (len(logbooktypes) + len(request.user.userprofile.active_logbooks())) > 1
    ):
        return HttpResponseRedirect(reverse("payment:pcloudy") + "?pack=addlogbook")

    # No logbooks ? -> Error
    if logbooktypes == []:
        messages.warning(request, "Aucun carnet sélectionné")
        return HttpResponseRedirect(reverse("logbooks:home"))

    # Create log books
    names = []
    logbooks_created = []

    for logbooktype in logbooktypes:
        logbook_class = book_settings.MAP[logbooktype]

        if logbook_class is None:
            msg = "Type de carnet: %s non disponible pour le moment" % (logbooktype)
            messages.warning(request, msg)
            return HttpResponseRedirect(reverse("logbooks:home"))

        # Check that name is unique, if not we append a counter
        name = LogBookBase.check_unique_name(
            log_book_class=logbook_class,
            user_id=request.user.id,
            name=settings.LOG_BOOKS_NAME_MAP[logbooktype],
        )
        book = logbook_class(name=name, ownr=request.user, cdate=datetime.now(), cat=logbooktype)
        try:
            book.save()
            names.append(name)
            logbooks_created.append(book)
        except ValidationError as exception:
            messages.warning(request, str(exception))
            return HttpResponseRedirect(reverse("logbooks:home"))

    if len(names) == 1:
        messages.success(request, "Le carnet %s vient d'être créé" % (names[0]))
    else:
        msg = "Les carnets %s viennent d'être créés" % (", ".join(names))
        messages.success(request, msg)
    return HttpResponseRedirect(reverse("logbooks:logbook", kwargs={"logbook_id": logbooks_created[0].id}))


# @user_has_plan(plan=1)
@fetch_logbook
@fetch_range_select("logbooks:totals")
def totals(request, logbook_id=None, template="logbooks/totals"):
    """
    Totals
    """
    logbook = request.logbook
    logbooks = request.logbooks
    if not logbook:
        raise Http404

    two_months_before_now = datetime.today() - timedelta(2 * 31)
    begin_date_raw = request.GET.get("begin_date", None)
    end_date_raw = request.GET.get("end_date", None)

    if begin_date_raw in [None, ""]:
        begin_date_raw = two_months_before_now
    if end_date_raw == "":
        end_date_raw = None

    full = False
    begin_date = None
    end_date = None

    if request.GET.get("select", "") == "lifetime":
        full = True
    else:
        begin_date, end_date = convert_str_to_date(begin_date_raw, end_date_raw)

    # Set endate to 23:59 9999 like in stats
    if end_date:
        end_date = datetime(day=end_date.day, month=end_date.month, year=end_date.year, **END_DAY_TIME)

    template = f"{template}_{logbook.cat}.html"

    totals_dict = logbook.get_totals(
        logbook.totals_page_totals(), time_slice=(begin_date, end_date), reports=full
    )

    return render(
        request,
        template,
        {
            "logbooks": logbooks,
            "logbook": logbook,
            "begin_date": begin_date,
            "full": full,
            "end_date": end_date,
            "totals": totals_dict,
        },
    )


# @user_has_plan(plan=1)
@fetch_logbook
def report(request, logbook_id=None, template="logbooks/report.html"):
    """
    Reports
    """
    logbook = request.logbook
    logbooks = request.logbooks

    form_class = logbook._report_form_model()

    if request.method == "POST":
        reportform = form_class(logbook, request.POST)
        if reportform.is_valid():
            logbook.reports = reportform.cleaned_data
            logbook.save()
            messages.success(request, "Report effectué.")
            return HttpResponseRedirect(reverse("logbooks:logbook", args=[logbook_id]))
    else:
        reportform = form_class(logbook, initial=logbook.reports)

    return render(
        request,
        template,
        {
            "logbooks": logbooks,
            "logbook": logbook,
            "reportform": reportform,
        },
    )


# @user_has_plan(plan=2)
@fetch_logbook
@fetch_range_select("logbooks:stats")
def stats(request, logbook_id=None, template="logbooks/stats"):
    """
    Stats
    """
    logbook = request.logbook
    logbooks = request.logbooks
    if not logbook:
        raise Http404

    template = f"{template}_{logbook.cat}.html"

    return render(
        request,
        template,
        {
            "logbooks": logbooks,
            "logbook": logbook,
            "disable_name": True,
        },
    )


@login_required
@fetch_logbook
def parameters(request, logbook_id=None, template="logbooks/parameters.html"):
    """
    Parameters
    """
    logbook = request.logbook
    logbooks = request.logbooks

    initial_data = {
        "name": logbook.name,
        "time_format": logbook.time_format,
        "height_format": logbook.height_format,
    }
    edit_lbook_form = EditLbookNameForm(initial=initial_data)
    delete_lbook_form = DeleteLbookForm()

    if logbook.can_fly:
        del edit_lbook_form.fields["height_format"]

    if request.method == "POST":
        form_picked = request.GET.get("f", "None")
        # DELETE
        if form_picked == "delete":
            delete_lbook_form = DeleteLbookForm(request.POST)
            if delete_lbook_form.is_valid():
                if delete_lbook_form.cleaned_data["should_delete"] is True:
                    dname = logbook.name
                    delete_lbook_form.delete(logbook, request.user.userprofile)
                    msg = "Le carnet %s vient d'être supprimé." % (dname)
                    messages.success(request, msg)
                    return HttpResponseRedirect(reverse("logbooks:home"))
        # RENAME
        else:
            edit_lbook_form = EditLbookNameForm(request.POST)
            if logbook.can_fly:
                del edit_lbook_form.fields["height_format"]

            if edit_lbook_form.is_valid():
                if not logbook.name == edit_lbook_form.cleaned_data["name"]:
                    edit_lbook_form.rename(logbook, request.user.id)
                    msg = "Le carnet vient d'être renommé en %s." % (logbook.name)
                    messages.success(request, msg)
                if not logbook.time_format == edit_lbook_form.cleaned_data["time_format"]:
                    logbook.time_format = edit_lbook_form.cleaned_data["time_format"]
                    logbook.save()
                    tf_name = TIME_FORMAT_CHOICES[logbook.time_format][1]
                    msg = "Le format de temps du carnet est maintenant %s." % (tf_name)
                    messages.success(request, msg)
                if (
                    not logbook.can_fly
                    and not logbook.height_format == edit_lbook_form.cleaned_data["height_format"]
                ):
                    logbook.height_format = edit_lbook_form.cleaned_data["height_format"]
                    logbook.save()
                    hf_name = HEIGHT_FORMAT_CHOICES[logbook.height_format][1]
                    msg = "Le format de temps du carnet est maintenant %s." % (hf_name)
                    messages.success(request, msg)
                return HttpResponseRedirect(reverse("logbooks:logbook", kwargs={"logbook_id": logbook_id}))

    return render(
        request,
        template,
        {
            "logbooks": logbooks,
            "logbook": logbook,
            "edit_lbook_form": edit_lbook_form,
            "delete_lbook_form": delete_lbook_form,
        },
    )


@login_required
@fetch_logbook
def add_log(request, logbook_id, log_id=None, template="logbooks/home"):
    """
    Create / Update a log
    """
    # If it's an ajax call we handle it separately
    if is_ajax(request):
        return _edit_live_log(request, logbook_id, log_id)

    try:
        page_nbr = int(request.GET.get("p", -1))
    except ValueError:
        page_nbr = -1

    # We bind some variables for the ease of use
    logbook = request.logbook
    log = None

    # Guardians
    if logbook.ownr != request.user and not request.user.is_staff and not request.user.is_superuser:
        return HttpResponseForbidden("Not yours")

    # We look for the log_id hidden field in the form data
    # If present it means we want an edit even if log_id from
    hidden_log_id = request.POST.get("log_id", None)
    if not log_id and hidden_log_id:
        log_id = hidden_log_id

    if log_id:
        log = LogBase.get_by_id(log_id)
        if not log:
            raise Http404("Ce vol n'existe pas")

        if log.lbook.id != logbook.id:
            return HttpResponseForbidden("Ce vol n'appartient pas au carnet")

    klass = logbook._log_form_model()
    # Should we show 'bon vol' or 'bon saut'
    fly_type = "vol"
    if not logbook.can_fly:
        fly_type = "saut"

    # Show the edition form for the requested log.
    if request.method == "GET":
        form = klass(logbook, log=log)
        return home(
            request,
            logbook_id=logbook_id,
            page_nbr=page_nbr,
            extra_context={"show_log_form": form},
        )

    # POST? Maybe an edit or an add
    if request.method == "POST":
        form = klass(logbook, request.POST, request.FILES, log)
        fobject = None
        add_file_after_log_save = False

        # Is form valid?
        if form.is_valid():
            log = form.save(request.user, logbook, request.FILES, log)
            if request.FILES:
                # Do we have enough space balance if free plan?
                if not request.user.userprofile.can_upload_media():
                    msg = "Votre escape de stockage pour ce pack est insuffisant."
                    messages.warning(request, msg)
                else:
                    f = request.FILES["media"]

                    # First store the file
                    fobject = FileModel(owner=request.user, file=f)
                    fobject.save()

                    add_file_after_log_save = True
                    # Then attach it to the log

            try:
                log.update = datetime.now()
                log.save()
                # Do we need to add a file ?
                if add_file_after_log_save and fobject:
                    log.files.add(fobject)

                # Valid!
                messages.success(
                    request,
                    "Le %s du %s est enregistré." % (fly_type, defaultfilters.date(log.date, "D d F Y")),
                )
            except (ValidationError,) as exception:
                messages.warning(request, f"Erreur de sauvegarde du {fly_type}: {exception!s}")

            # We finally redirect the end user to the final page
            return HttpResponseRedirect(
                reverse("logbooks:logbook", kwargs={"logbook_id": logbook_id}) + "?p=%s" % page_nbr
            )

    # Not valid
    return home(request, logbook_id=logbook_id, page_nbr=page_nbr, extra_context={"show_log_form": form})


@require_POST
def _edit_live_log(request, logbook_id, log_id):
    """
    Edit log from an Ajax request
    Returns JSON
    """

    logbook = request.logbook

    # Guardians
    if logbook.ownr != request.user and not request.user.is_staff and not request.user.is_superuser:
        return json_fail("Not yours")

    # get log and check if it exists and belong to the log book
    log = LogBase.get_by_id(log_id)

    if not log:
        return json_fail("Ce vol n'existe pas")

    if log.lbook.id != logbook.id:
        return json_fail("Ce vol n'appartient pas au carnet")

    # Update date
    log.update = datetime.now()

    # FILE UPLOAD
    # Is it an Ajax file upload .
    # the file is stored raw in the request
    if "qqfile" in request.GET:
        uploaded = request
        filename = request.GET["qqfile"]

        new_file = ContentFile(uploaded.raw_post_data)

        time_string = str(time.time())
        base, ext = path.splitext(filename)
        final = f"{base}[{time_string}]{ext}"
        new_file.name = final

        # Do we have enough disk space balance on free plan ?
        if not request.user.userprofile.can_upload_media():
            msg = "Votre escape de stockage pour ce pack est insuffisant."
            messages.warning(request, msg)
        else:
            # Create a file
            fobject = FileModel(owner=request.user, file=new_file)
            fobject.save()
            log.files.add(fobject)

            log.save()

        # return helpful data for the QQ uploader
        data = {"url": fobject.file.url, "fname": final[:14] + "...", "size": new_file.size / 1000}
        return json_ok(data)

    # STANDARD UPDATE
    # checking that wanted params are present
    if "field" not in request.POST or "val" not in request.POST:
        return json_fail("Field param not present")

    new_value = request.POST["val"]
    field = request.POST["field"]

    if not _live_edit_field_allowed(log, field):
        return json_fail("Champ non modifiable")

    if getattr(logbook, "cat", "") == "plane_fcl1080" and field in {
        "departure_place",
        "arrival_place",
        "airpdep",
        "airpar",
    }:
        new_value = icao_from_place(new_value)

    # Special case for date we need to create a dateTimeObject
    if field == "date":
        mydate = time.strptime(new_value, "%Y-%m-%d")
        new_value = datetime(*mydate[:3])

    try:
        setattr(log, field, new_value)
        log.save()

    except AttributeError:
        return json_fail("Attribute does not exist")
    except ValidationError as exp:
        return json_fail("Erreur de sauvegarde du vol: %s" % (str(exp)))
    return json_ok()


@login_required
def create_aeronef(request, logbook_id=None, template="logbooks/create_aeronef.html"):
    logbooks = request.user.userprofile.active_logbooks()

    return render(
        request,
        template,
        {
            "logbooks": logbooks,
        },
    )


@login_required
@fetch_logbook
def export(request, logbook_id, ex_type):
    """
    Export logbook to pdf or csv
    """
    valid_types = ["csv", "pdf"]
    if ex_type not in valid_types:
        return HttpResponseForbidden("Format unknown")

    logbook = request.logbook

    # Export pdf
    if ex_type == "pdf":
        show_cuts = False
        if "mode" in request.GET:
            if request.GET["mode"] == "show_cuts":
                show_cuts = True

        if request.user.userprofile.plan == 1:
            return redirect(reverse("payment:pcloudy") + "?pack=export_logbook")

        # TODO: not sure we need to pass an HttpResponse we
        # just want the data, we could call to_pdf()
        response = HttpResponse(content_type="application/pdf")
        logbook.attach_pdf_to_http_response(
            http_response=response, title=str(slugify(logbook.name)), show_cuts=show_cuts
        )

    # Export csv
    if ex_type == "csv":
        response = HttpResponse(content_type="text/csv")
        logbook.attach_csv_to_http_response(response)

    response["Content-Disposition"] = "attachment; filename={}_{}_{}.{}".format(
        slugify(logbook.cat),
        slugify(logbook.name),
        datetime.now().strftime("%d-%m-%y"),
        ex_type,
    )
    return response


@login_required
@fetch_logbook
def import_processing(request, logbook_id, template="import_processing.html"):
    logbook = request.logbook
    context = {
        "logbooks": request.logbooks,
        "logbook": request.logbook,
    }
    # Render!
    return render(request, template, context)


@login_required
@fetch_logbook
def import_home(request, logbook_id, template="logbooks/import_home.html"):
    logbook = request.logbook

    form = FileCommentsForm()

    if request.method == "POST":
        form = FileCommentsForm(request.POST, request.FILES)
        if form.is_valid():
            fname = form.send_file_to_manager(request.FILES["data_file"], request.user, logbook)
            messages.success(request, "Fichier %s envoyé pour import" % fname)
            return HttpResponseRedirect(
                reverse("logbooks:import_processing", kwargs={"logbook_id": logbook_id})
            )

    context = {
        "logbooks": request.logbooks,
        "logbook": request.logbook,
        "aform": form,
        "first_class": request.user.userprofile.has_payed_plan(),
    }
    return render(request, template, context)


@login_required
@fetch_logbook
def import_auto(request, logbook_id):
    logbook = request.logbook
    errors = []

    if request.method == "POST":
        form = AutoImportForm(request.POST, request.FILES)

        if form.is_valid():
            f = request.FILES.get("data_file")

            # Store the file to a temporary place.
            output = tempfile.NamedTemporaryFile(delete=False)
            output_path = output.name
            destination = pathlib.Path(output_path).open("wb+")
            for chunk in f.chunks():
                destination.write(chunk)
            destination.close()

            tim = form.cleaned_data["minutes_only"]
            result = logbook.import_from_csv(output_path, delimiter=";", time_in_min=tim)

            if result["success"] is True:
                messages.success(request, "Import effectué.")
                return redirect(reverse("logbooks:logbook", args=[logbook.id]))

            errors = form._errors.setdefault("data_file", ErrorList())
            errors.append(result["message"])

    else:
        form = AutoImportForm()

    context = {
        "logbooks": request.logbooks,
        "logbook": request.logbook,
        "aform": form,
    }
    return render(request, "logbooks/import_auto.html", context)


@login_required
@require_POST
@fetch_logbook
def del_log(request, logbook_id, log_id):
    """
    Flag a log as deleted
    """
    # Do not forget to use get_by_id insteand of
    # get_object_or_404 since we need to look
    # at the content type to fetch the good logbook/log
    try:
        logbook = LogBookBase.get_by_id(logbook_id)
    except LogBookBase.DoesNotExist:
        raise Http404

    try:
        log = LogBase.get_by_id(log_id)
    except LogBase.DoesNotExist:
        raise Http404

    # Guardians
    if logbook.ownr != request.user and not request.user.is_staff and not request.user.is_superuser:
        return json_fail("Not yours")

    if log.lbook.id != logbook.id:
        return json_fail("Ce vol n'appartient pas au carnet")

    log.deleted = True
    log.save()

    msg = "Le vol du %s est supprimé" % defaultfilters.date(log.date, "D d F Y")
    messages.success(request, msg)

    return json_ok()
