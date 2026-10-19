import random
import string
from datetime import date

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.forms import SelectDateWidget
from django.utils.translation import gettext_lazy as _
from django_registration.forms import RegistrationForm

from cloudy.accounts.models import ProfileSettings
from cloudy.core.fields import HoneypotField
from cloudy.notifications.models import NOTICE_MEDIA_DEFAULTS, NoticeSetting, NoticeType

MIN_PILOT_AGE = 14
MAX_PILOT_AGE = 100


def birth_date_year_range(min_age=MIN_PILOT_AGE, max_age=MAX_PILOT_AGE):
    today = date.today()
    return range(today.year - min_age, today.year - max_age - 1, -1)


def birth_date_select_widget():
    return SelectDateWidget(years=birth_date_year_range())


def validate_minimum_pilot_age(dob, min_age=MIN_PILOT_AGE):
    today = date.today()
    age = today.year - dob.year
    if today < dob.replace(year=today.year):
        age -= 1
    if age < min_age:
        raise forms.ValidationError(_("Vous devez avoir au moins %(age)s ans.") % {"age": min_age})


def generate_username(last_name: str) -> str:
    for _attempt in range(10):
        suffix = "".join(random.choice(string.ascii_letters) for _char in range(5))
        username = f"{last_name}-{suffix}"
        if not User.objects.filter(username=username).exists():
            return username
    raise forms.ValidationError(_("Impossible de générer un identifiant unique, veuillez réessayer."))


class LoginForm(forms.Form):
    redirect_to = forms.CharField(widget=forms.HiddenInput, required=False)

    email = forms.CharField(
        label=_("Email"),
        max_length=100,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )
    password = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={"class": "input-medium"}),
    )
    remember = forms.BooleanField(
        label=_("Mémoriser"),
        help_text=_("Cochez pour rester connecté pendant trois semaines."),
        required=False,
    )

    user = None  # allow access to user object

    def clean(self):
        if self._errors:
            return
        low_email = self.cleaned_data["email"].lower()
        user = authenticate(email=low_email, password=self.cleaned_data["password"])
        if not user:
            user = authenticate(username=low_email, password=self.cleaned_data["password"])
        if user:
            if user.is_active:
                self.user = user
            else:
                raise forms.ValidationError(_("Ce compte n'est pas activé."))
        else:
            raise forms.ValidationError(_("L'email et/ou le mot de passe spécifiés ne sont pas correctes."))
        return self.cleaned_data

    def login(self, request):
        if self.is_valid():
            login(request, self.user)

            messages.add_message(
                request,
                messages.INFO,
                _("Vous êtes Connecté en tant que %(name)s.") % {"name": self.user.get_full_name()},
            )

            if self.cleaned_data["remember"]:
                request.session.set_expiry(60 * 60 * 24 * 7 * 3)
            else:
                request.session.set_expiry(0)
            return True
        return False


class CloudyRegistrationForm(RegistrationForm):
    # # fake field
    website = HoneypotField(initial="")

    first_name = forms.CharField(
        label=_("Prénom"),
        max_length=30,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )

    last_name = forms.CharField(
        label=_("Nom"),
        max_length=30,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )

    dob = forms.DateField(
        label="Date de naissance",
        widget=birth_date_select_widget(),
    )
    email = forms.EmailField(
        widget=forms.TextInput(attrs={"class": "input-long", "maxlength": 75}), label=_("Email")
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(render_value=False, attrs={"class": "input-medium"}),
        label=_("Mot de passe"),
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(render_value=False, attrs={"class": "input-medium"}),
        label=_("Confirmation mot de passe"),
    )
    tos = forms.BooleanField(
        widget=forms.CheckboxInput(),
        label=_("j'accept les conditions générales d'utilisation du site"),
        error_messages={"required": _("Vous devez accepter les conditions générales d'utilisation !")},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("username", None)

    def step1_fields(self):
        """
        To help divide form in steps (not wizard)
        """
        _list = ["website", "first_name", "last_name", "dob", "email", "password1", "password2"]
        return map(lambda x: self[x], _list)

    def step3_fields(self):
        """
        To help divide form in steps (not wizard)
        """
        _list = ["tos"]
        return map(lambda x: self[x], _list)

    def clean_first_name(self):
        return self.cleaned_data["first_name"].capitalize()

    def clean_last_name(self):
        return self.cleaned_data["last_name"].upper()

    def clean_dob(self):
        dob = self.cleaned_data["dob"]
        validate_minimum_pilot_age(dob)
        return dob

    def clean_email(self):
        email = self.cleaned_data.get("email", None)
        if email and User.objects.filter(email=email).count():
            raise forms.ValidationError("Cet email est déjà enregistré.")
        return email

    def clean(self):
        cleaned_data = super().clean()

        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")
        if first_name and last_name:
            if User.objects.filter(first_name=first_name, last_name=last_name).exists():
                raise forms.ValidationError(
                    _(
                        "Un utilisateur avec le même nom et le même prénom existe déjà dans notre base ! En case de soucis, veuillez contacter le support."
                    )
                )

        if last_name:
            self.instance.username = generate_username(last_name)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if not user.username:
            user.username = generate_username(user.last_name)
        user = self.set_password_and_save(user, commit=commit)
        if commit and hasattr(self, "save_m2m"):
            self.save_m2m()
        return user


class SetPasswordStyledForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label=_("New password"), widget=forms.PasswordInput(attrs={"class": "input-medium"})
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        widget=forms.PasswordInput(attrs={"class": "input-medium"}),
    )


class CloudyAccountForm(forms.Form):
    """
    Account form to edit user profile
    """

    first_name = forms.CharField(
        label=_("Prénom"),
        max_length=30,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )
    last_name = forms.CharField(
        label=_("Nom"),
        max_length=30,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )
    email = forms.EmailField(
        widget=forms.TextInput(attrs={"class": "input-long", "maxlength": 75}), label=_("Email")
    )
    dob = forms.DateField(
        label="Date de naissance",
        widget=birth_date_select_widget(),
    )

    photo = forms.ImageField(
        required=False,
        label="Photo de profil",
        help_text="Image JPG ou PNG",
    )

    phone = forms.CharField(
        required=False,
        label="Numéro de mobile",
        help_text=" ",
        widget=forms.TextInput(attrs={"class": "input-medium"}),
        max_length=12,
    )

    aerodrom = forms.CharField(
        required=False,
        label="Aérodrome",
        help_text="(code OACI)",
        max_length=30,
        widget=forms.TextInput(attrs={"class": "input-medium"}),
    )

    def clean_dob(self):
        dob = self.cleaned_data["dob"]
        validate_minimum_pilot_age(dob)
        return dob

    def save(self, user, files):
        """
        Update user profile
        """
        data = self.cleaned_data.copy()
        user.first_name = data["first_name"]
        user.last_name = data["last_name"]
        user.email = data["email"]
        user.userprofile.phone = data["phone"]
        user.userprofile.dob = data["dob"]
        user.userprofile.aerodrom = data["aerodrom"]
        user.userprofile.phone = data["phone"]
        if "photo" in files:
            user.userprofile.avatar = files["photo"]
        user.userprofile.save()
        user.save()


class ProfileSettingsForm(forms.ModelForm):
    """
    Profile model form
    """

    class Meta:
        model = ProfileSettings
        exclude = ("user",)

    def save(self, user):
        """Get notification settings and update them accordingly"""
        mail_on_notif = self.cleaned_data["mail_on_notification"]

        # get all types and update notice settings
        types = NoticeType.objects.all()
        for notice_type in types:
            if notice_type.label not in settings.NOTICE_TYPE_IGNORE:
                try:
                    notice_setting = NoticeSetting.for_user(user, notice_type, 0)
                    notice_setting.send = mail_on_notif
                    notice_setting.save()
                except KeyError:
                    raise ValueError(
                        "Something is misconfigured with the notification backend: "
                        + str(NOTICE_MEDIA_DEFAULTS)
                    )

        # save setting
        p, created = ProfileSettings.objects.get_or_create(user=user)
        p.mail_on_notification = mail_on_notif
        p.save()
