"""
Some useful views decorators.
"""

try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps  # Python 2.4 fallback.

from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.urls import reverse


# Check authorization for the plan
def user_has_plan(plan=1):
    """
    This function tests the level of privilege for the current user.
    - plan=1 is basically "is user logged?" because the lowest level of
      privileges is 1.
    - See PLAN_CHOICES /accounts/models.py for the detailled levels.

    Based on Django's /django/contrib/auth/decorators.py user_passes_test.

    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # We check if the user is authenticated
            if not request.user.is_authenticated:
                path = request.build_absolute_uri()
                return redirect_to_login(path, reverse("auth_login"))

            # Then we check its privilege level
            if request.user.userprofile.plan >= plan:
                return view_func(request, *args, **kwargs)

            # This user does not have enough privileges. Upgrade?
            # return redirect('unpaidtease', frm=view_func.__name__)
            return redirect(reverse("payment:pcloudy") + "?pack=%s" % (view_func.__name__))

        return _wrapped_view

    return decorator
