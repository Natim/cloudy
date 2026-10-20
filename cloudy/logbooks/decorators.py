import json

from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from cloudy.core.utils import is_ajax
from cloudy.logbooks.models import LogBookBase


def fetch_logbook(f):
    """
    Check that the method has logbook_id as params
    Get the logbook matching the params if valid and attach it to
    the request object.
    Admins can see whoever logbook
    """

    def wrap(request, *args, **kwargs):
        # AnonymousUser has no numeric id. Django 6 rejects it as a foreign key.
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        # Grab the id of the logbook.
        logbook_id = kwargs.get("logbook_id", None)

        # Grab all the active logbooks of the user in order to display them
        # above the action bar.
        logbooks = LogBookBase.existing_for_user(request.user)

        # Grab the current logbook
        logbook = None
        if logbook_id is not None:
            logbook = LogBookBase.get_by_id(logbook_id)

        # We have to check if it belongs to the user.
        # But we do remember that admins are like god.
        if logbook is not None:
            if not (request.user.is_staff or request.user.is_superuser):
                if not logbook.ownr == request.user:
                    # If this is an ajax request, we return a special answer.
                    if is_ajax(request):
                        return HttpResponse(
                            json.dumps({"success": False, "msg": "Ce carnet n'existe pas"}),
                            content_type="application/json",
                        )
                    # If it's a normal query, we redirect to the home.
                    # FIXME : why don't we display a 404 page?
                    return HttpResponseRedirect(reverse("logbooks:home"))

        # Now we check if the user can add new logbooks in order to display
        # some error messages if he tries to.
        request.can_add_logbooks = True
        if len(logbooks) > 1 and not request.user.userprofile.has_payed_plan():
            request.can_add_logbooks = False

        # If the user does not have ANY logbook AT ALL:
        if len(logbooks) == 0:
            # We set logbook(s) to None
            request.logbook = None
            request.logbooks = None
        # If the user has not selected a logbook but has some, we pick the first

        if (logbook is None or not logbook.visbl) and len(logbooks) > 0:
            logbook = logbooks[0]

        # We bind the logbooks to the request object
        request.logbooks = logbooks
        request.logbook = logbook

        # And now we execute the decorated function
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def fetch_range_select(redirect_reverse=""):
    """
    look for select/date begin/end values from session
    If nothing is there we set it to the current selection
    otherwise if no select is present in the GET vars we use
    tho one from sessions.
    This allows us to move from totals to stats page while keeping
    the same range selection.
    """

    def decorator(view_func):
        def wrap(request, *args, **kwargs):
            select_val = request.GET.get("select")
            logbook = request.logbook
            begin_date_raw = request.GET.get("begin_date")
            end_date_raw = request.GET.get("end_date")

            if not select_val:
                stored_begin_date = request.session.get("range_begin_date")
                stored_end_date = request.session.get("range_end_date")
                stored_select_val = request.session.get("range_select_val")

                if stored_select_val:
                    # build get params
                    get_str = "?select=%s" % (stored_select_val)
                    if stored_begin_date:
                        get_str += "&begin_date=%s" % (stored_begin_date)
                    if stored_end_date:
                        get_str += "&end_date=%s" % (stored_end_date)
                    # redirect
                    return HttpResponseRedirect(
                        reverse(
                            redirect_reverse,
                            args=[
                                logbook.id,
                            ],
                        )
                        + get_str
                    )

            else:
                # store range in session
                if "range_begin_date" in request.session:
                    del request.session["range_begin_date"]
                if "range_end_date" in request.session:
                    del request.session["range_end_date"]
                if begin_date_raw:
                    request.session["range_begin_date"] = begin_date_raw
                if end_date_raw:
                    request.session["range_end_date"] = end_date_raw
                request.session["range_select_val"] = select_val
                # And now we execute the decorated function

            return view_func(request, *args, **kwargs)

        return wrap

    return decorator


def fetch_logbook(f):
    """
    Check that the method ha logbook_id as params
    Get the logbook matching the params if valid and attach it to
    the request object.
    Admins can see whoever logbook
    """

    def wrap(request, *args, **kwargs):
        # AnonymousUser has no numeric id. Django 6 rejects it as a foreign key.
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        # Grab the id of the logbook.
        logbook_id = kwargs.get("logbook_id", None)

        # Grab all the active logbooks of the user in order to display them
        # above the action bar.
        logbooks = LogBookBase.existing_for_user(request.user)

        # Grab the current logbook
        logbook = None
        if logbook_id is not None:
            logbook = LogBookBase.get_by_id(logbook_id)

        # We have to check if it belongs to the user.
        # But we do remember that admins are like god.
        if logbook is not None:
            if not (request.user.is_staff or request.user.is_superuser):
                if logbook.ownr != request.user:
                    # If this is an ajax request, we return a special answer.
                    if is_ajax(request):
                        return HttpResponse(
                            json.dumps({"success": False, "msg": "Ce carnet n'existe pas"}),
                            content_type="application/json",
                        )
                    # If it's a normal query, we redirect to the home.
                    # FIXME : why don't we display a 404 page?
                    return HttpResponseRedirect(reverse("logbooks:home"))

        # Now we check if the user can add new logbooks in order to display
        # some error messages if he tries to.
        request.can_add_logbooks = True
        if len(logbooks) > 1 and not request.user.userprofile.has_payed_plan():
            request.can_add_logbooks = False

        # If the user does not have ANY logbook AT ALL:
        if len(logbooks) == 0:
            # We set logbook(s) to None
            request.logbook = None
            request.logbooks = None
        # If the user has not selected a logbook but has some, we pick the first

        if (logbook is None or not logbook.visbl) and len(logbooks) > 0:
            logbook = logbooks[0]

        # We bind the logbooks to the request object
        request.logbooks = logbooks
        request.logbook = logbook

        # And now we execute the decorated function
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def fetch_range_select(redirect_reverse=""):
    """
    look for select/date begin/end values from session
    If nothing is there we set it to the current selection
    otherwise if no select is present in the GET vars we use
    tho one from sessions.
    This allows us to move from totals to stats page while keeping
    the same range selection.
    """

    def decorator(view_func):
        def wrap(request, *args, **kwargs):
            select_val = request.GET.get("select", None)
            logbook = request.logbook
            begin_date_raw = request.GET.get("begin_date", None)
            end_date_raw = request.GET.get("end_date", None)

            if not select_val:
                stored_begin_date = request.session.get("range_begin_date", None)
                stored_end_date = request.session.get("range_end_date", None)
                stored_select_val = request.session.get("range_select_val", None)

                if stored_select_val:
                    # build get params
                    get_str = "?select=%s" % (stored_select_val)
                    if stored_begin_date:
                        get_str += "&begin_date=%s" % (stored_begin_date)
                    if stored_end_date:
                        get_str += "&end_date=%s" % (stored_end_date)
                    # redirect
                    return HttpResponseRedirect(
                        reverse(
                            redirect_reverse,
                            args=[
                                logbook.id,
                            ],
                        )
                        + get_str
                    )

            else:
                # store range in session
                if "range_begin_date" in request.session:
                    del request.session["range_begin_date"]
                if "range_end_date" in request.session:
                    del request.session["range_end_date"]
                if begin_date_raw:
                    request.session["range_begin_date"] = begin_date_raw
                if end_date_raw:
                    request.session["range_end_date"] = end_date_raw
                request.session["range_select_val"] = select_val
                # And now we execute the decorated function

            return view_func(request, *args, **kwargs)

        return wrap

    return decorator
