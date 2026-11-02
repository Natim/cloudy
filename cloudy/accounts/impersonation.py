import logging

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from cloudy.accounts.models import UserProfile

logger = logging.getLogger(__name__)

IMPERSONATOR_SESSION_KEY = "impersonator_id"
AUTH_BACKEND = "django.contrib.auth.backends.ModelBackend"


def impersonation_context(request):
    session = getattr(request, "session", None)
    if session is None:
        return {}
    return {"impersonator_id": session.get(IMPERSONATOR_SESSION_KEY)}


def can_impersonate(actor, target):
    return (
        actor.is_authenticated
        and actor.is_superuser
        and actor.is_active
        and target.is_active
        and not target.is_staff
        and not target.is_superuser
        and target.pk != actor.pk
    )


def _login_preserving_last_login(request, user):
    previous_last_login = user.last_login
    login(request, user, backend=AUTH_BACKEND)
    User.objects.filter(pk=user.pk).update(last_login=previous_last_login)


@require_POST
@login_required
def impersonate(request, user_id):
    """Open the site as another user, remembering the superuser who started it."""
    if not request.user.is_superuser or request.session.get(IMPERSONATOR_SESSION_KEY):
        return HttpResponseForbidden()

    target = get_object_or_404(User, pk=user_id)
    if not can_impersonate(request.user, target):
        return HttpResponseForbidden()

    impersonator_id = request.user.pk
    _login_preserving_last_login(request, target)
    # login() replaces the session when the user changes, so the marker is set after.
    request.session[IMPERSONATOR_SESSION_KEY] = impersonator_id
    logger.info("user %s started impersonating user %s", impersonator_id, target.pk)
    return redirect("logbooks:home")


@require_POST
@login_required
def stop_impersonation(request):
    """Return the browser session to the superuser who started impersonation."""
    impersonator_id = request.session.get(IMPERSONATOR_SESSION_KEY)
    if not impersonator_id:
        return HttpResponseForbidden()

    impersonator = User.objects.filter(pk=impersonator_id, is_active=True, is_superuser=True).first()
    if impersonator is None:
        return HttpResponseForbidden()

    profile = UserProfile.objects.filter(user_id=request.user.pk).first()
    _login_preserving_last_login(request, impersonator)
    logger.info("user %s stopped impersonating", impersonator.pk)
    if profile is not None:
        return redirect("admin:accounts_userprofile_change", profile.pk)
    return redirect("admin:index")
