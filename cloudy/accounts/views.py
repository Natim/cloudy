# from django_registration.backends import get_backend

from constance import config
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_GET, require_POST
from django_registration.backends.activation.views import RegistrationView as ActivationRegistrationView

from cloudy.accounts.decorators import user_has_plan

# from notification import models as notification  # DELETE
# from annoying.decorators import render_to  # DELETE
from cloudy.accounts.forms import (
    CloudyAccountForm,
    CloudyRegistrationForm,
    LoginForm,
    ProfileSettingsForm,
    SetPasswordStyledForm,
)
from cloudy.accounts.models import ProfileSettings, UserProfile

# from cloudy.payment.payline_processor import PaylineProcessor
# from cloudy.payment.models import Purchase
# from cloudy.payment.signals import paid_registration_complete, free_registration_complete


class CloudyRegistrationView(ActivationRegistrationView):
    form_class = CloudyRegistrationForm
    template_name = "accounts/registration_form.html"

    def registration_allowed(self):
        return bool(config.SIGNUP_AUTHORIZED)

    def create_inactive_user(self, form):
        new_user = form.save(commit=False)
        new_user.is_active = False
        new_user.save()

        profile = UserProfile(user=new_user, dob=form.cleaned_data["dob"])
        profile.generate_api_key()
        profile.save()

        self.send_activation_email(new_user)
        return new_user

    def get_success_url(self, user=None):
        url = super().get_success_url(user)
        if user and user.email:
            return f"{url}?{urlencode({'email': user.email})}"
        return url


def login(request, template_name):
    from django.utils.http import url_has_allowed_host_and_scheme

    redirect_to = request.GET.get("next", reverse("logbooks:home"))
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.login(request):
            redirect_to = request.POST.get("redirect_to", reverse("logbooks:home"))
            if not redirect_to:
                redirect_to = reverse("logbooks:home")
            if not url_has_allowed_host_and_scheme(
                url=redirect_to,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                redirect_to = reverse("logbooks:home")
            return HttpResponseRedirect(redirect_to)
    else:
        form = LoginForm(initial={"redirect_to": redirect_to})

    return render(request, template_name, {"form": form})


@login_required
def profile(request, template="profile.html"):
    """
    Profile page
    Edit user info
    """
    if request.method == "POST":
        form = CloudyAccountForm(request.POST, request.FILES)
        if form.is_valid():
            form.save(request.user, request.FILES)
            messages.success(request, "Profil mis à jour")
            return HttpResponseRedirect("")
    else:
        u = request.user
        udata = {
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "dob": u.userprofile.dob,
            "phone": u.userprofile.phone,
            "aerodrom": u.userprofile.aerodrom,
        }
        form = CloudyAccountForm(initial=udata)

    return render(request, template, {"form": form})


@require_GET
@login_required
def account_admin(request, template="account_admin.html"):
    """
    Account admin page
    """
    p, created = ProfileSettings.objects.get_or_create(user=request.user)
    settings_form = ProfileSettingsForm(instance=p)
    passwd_form = SetPasswordStyledForm(request.user)

    return render(
        request,
        template,
        {
            "passwd_form": passwd_form,
            "settings_form": settings_form,
        },
    )


@require_POST
@login_required
def account_admin_settings(request, template="account_admin.html"):
    """
    Account admin page
    - Notifications setting
    """
    if request.method == "POST":
        settings_form = ProfileSettingsForm(request.POST)
        if settings_form.is_valid():
            settings_form.save(request.user)
            messages.success(request, "Configuration des alertes confirmée")
            return HttpResponseRedirect(reverse("account_admin"))

    passwd_form = SetPasswordStyledForm(request.user)
    return render(
        request,
        template,
        {
            "passwd_form": passwd_form,
            "settings_form": settings_form,
        },
    )


@require_POST
@login_required
def account_admin_passwd(request, template="account_admin.html"):
    """
    Account admin page
    - Password reset
    """
    if request.method == "POST":
        passwd_form = SetPasswordStyledForm(request.user, request.POST)
        if passwd_form.is_valid():
            passwd_form.save()
            messages.success(request, "Mot de passe mis à jour")
            return HttpResponseRedirect(reverse("account_admin"))

    settings_form = ProfileSettingsForm()
    return render(
        request,
        template,
        {
            "passwd_form": passwd_form,
            "settings_form": settings_form,
        },
    )


# Override register view from registration app
# We want to use several forms.
def register(
    request,
    backend,
    success_url=None,
    success_url_payed=None,
    disallowed_url="registration_disallowed",
    template_name="registration/registration_form.html",
    extra_context=None,
):
    """
    Allow a new user to register an account.

    The actual registration of the account will be delegated to the
    backend specified by the ``backend`` keyword argument (see below);
    it will be used as follows:

    1. The backend's ``registration_allowed()`` method will be called,
       passing the ``HttpRequest``, to determine whether registration
       of an account is to be allowed; if not, a redirect is issued to
       the view corresponding to the named URL pattern
       ``registration_disallowed``. To override this, see the list of
       optional arguments for this view (below).

    2. The form to use for account registration will be obtained by
       calling the backend's ``get_form_class()`` method, passing the
       ``HttpRequest``. To override this, see the list of optional
       arguments for this view (below).

    3. If valid, the form's ``cleaned_data`` will be passed (as
       keyword arguments, and along with the ``HttpRequest``) to the
       backend's ``register()`` method, which should return the new
       ``User`` object.

    4. Upon successful registration, the backend's
       ``post_registration_redirect()`` method will be called, passing
       the ``HttpRequest`` and the new ``User``, to determine the URL
       to redirect the user to. To override this, see the list of
       optional arguments for this view (below).

    **Required arguments**

    None.

    **Optional arguments**

    ``backend``
        The dotted Python import path to the backend class to use.

    ``disallowed_url``
        URL to redirect to if registration is not permitted for the
        current ``HttpRequest``. Must be a value which can legally be
        passed to ``django.shortcuts.redirect``. If not supplied, this
        will be whatever URL corresponds to the named URL pattern
        ``registration_disallowed``.

    ``form_class``
        The form class to use for registration. If not supplied, this
        will be retrieved from the registration backend.

    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context.

    ``success_url``
        URL to redirect to after successful registration. Must be a
        value which can legally be passed to
        ``django.shortcuts.redirect``. If not supplied, this will be
        retrieved from the registration backend.

    ``template_name``
        A custom template to use. If not supplied, this will default
        to ``registration/registration_form.html``.

    **Context:**

    ``form``
        The registration form.

    Any extra variables supplied in the ``extra_context`` argument
    (see above).

    **Template:**

    registration/registration_form.html or ``template_name`` keyword
    argument.

    ====================
    Extra (cloudy):

    This modified version uses a hardcoded signup form and payment form
    TODO: integrate it generically to the backend

    """
    # Redirect
    if not request.user.is_anonymous:
        logout(request)

    # backend = get_backend(backend)  # TODO
    # if not backend.registration_allowed(request):
    #     return redirect(disallowed_url)

    form_class = CloudyRegistrationForm

    if request.method == "POST":
        form = form_class(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_user = backend.register(request, **form.cleaned_data)
            # free_registration_complete.send(new_user)  # TODO
            if success_url is None:
                to, args, kwargs = backend.post_registration_redirect(request, new_user)
                return redirect(f"{reverse(to)}?{urlencode({'email': new_user.email})}", *args, **kwargs)
            else:
                return redirect(success_url)
        else:
            raise ValueError(f"{form.errors}")
    else:
        form = form_class()

    context = {"form": form, "can_signup": config.SIGNUP_AUTHORIZED}
    if extra_context:
        for key, value in extra_context.items():
            context[key] = value() if callable(value) else value

    return render(request, template_name, context)


# *** Test views


@user_has_plan(1)
def test_authorization_decorator(request):
    return HttpResponse("", status=402)


@user_has_plan(2)
def test_authorization_decorator_first(request):
    return HttpResponse("", status=402)
