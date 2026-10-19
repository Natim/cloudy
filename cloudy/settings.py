"""
Django settings for cloudy project.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _running_under_pytest() -> bool:
    return any(Path(arg).name in {"pytest", "py.test"} for arg in sys.argv if arg)


_INSECURE_SECRET_PREFIX = "django-insecure-"
SECRET_KEY = env("DJANGO_SECRET_KEY", f"{_INSECURE_SECRET_PREFIX}dev-only-change-me")
_using_dev_secret = SECRET_KEY.startswith(_INSECURE_SECRET_PREFIX)
# Explicit DJANGO_DEBUG wins; otherwise enable DEBUG under pytest or with the dev placeholder secret.
DEBUG = env_bool("DJANGO_DEBUG", _running_under_pytest() or _using_dev_secret)

if not DEBUG and (not SECRET_KEY or _using_dev_secret):
    raise ImproperlyConfigured(
        "Set DJANGO_SECRET_KEY to a unique non-placeholder value when DJANGO_DEBUG is false."
    )

ALLOWED_HOSTS = env(
    "DJANGO_ALLOWED_HOSTS", "www.cloudy.fr,cloudy.fr,api.cloudy.fr,localhost,127.0.0.1"
).split(",")

ADMINS = ["contact@cloudy.fr"]
MANAGERS = ["contact@cloudy.fr"]
UNKNOWN_AIRPORTS_CONTACTS = ["contact@cloudy.fr"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Production carries a populated django_site row and the URL shortener resolves
    # the public domain through Site.objects.get_current().
    "django.contrib.sites",
    "constance",
    "compressor",
    "easy_thumbnails",
    "analytical",
    "django_registration",
    "cloudy.notifications",
    "cloudy.alerts",
    "cloudy.accounts.apps.AccountsConfig",
    "cloudy.core",
    "cloudy.faq",
    "cloudy.logbooks",
    "cloudy.press",
    "cloudy.quotes",
    "cloudy.time_format",
    "cloudy.height_format",
    "cloudy.stats",
    "cloudy.imports",
    "cloudy.urlshortener",
    "cloudy.payment",
    "cloudy.optional_filter_choices",
    "cloudy.aircrafts",
    "cloudy.couponning",
    "cloudy.crons",
    "cloudy.DGAC_avion_logbook",
    "cloudy.DGAC_ballon_logbook",
    "cloudy.DGAC_planeur_logbook",
    "cloudy.FCL1080",
    "cloudy.FFPLUM_ulm_logbook",
    "cloudy.FFP_logbook",
]

ACCOUNT_ACTIVATION_DAYS = 7
AUTHENTICATION_BACKENDS = [
    "cloudy.accounts.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
# Django's default same-origin policy omits Referer on OSM tile requests; they 403.
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

if not DEBUG:
    SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", True)
    CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", True)
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
    SECURE_HSTS_SECONDS = int(env("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", True)

ROOT_URLCONF = "cloudy.urls"
WSGI_APPLICATION = "cloudy.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "cloudy" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.static",
                "django.template.context_processors.media",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
database_url = env("DATABASE_URL")
if database_url.startswith("postgres"):
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "cloudy_scratch"),
        "USER": env("POSTGRES_USER", "cloudy"),
        "PASSWORD": env("POSTGRES_PASSWORD", "cloudypwd"),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
    }

# Gates the redis-backed pagination and stats caches in cloudy.logbooks.paginator,
# cloudy.stats.models and cloudy.stats.views. Those modules read settings.CACHING
# unconditionally, so it has to exist; when off they recompute instead.
CACHING = env_bool("CACHING", False)

REDIS_SERVER = env("REDIS_HOST", "localhost")
REDIS_PORT = int(env("REDIS_PORT", "6379"))
REDIS_DB = int(env("REDIS_DB", "4"))
REDIS_PASSWORD = env("REDIS_PASSWORD") or None

CONSTANCE_BACKEND = "constance.backends.redisd.RedisBackend"
CONSTANCE_REDIS_CONNECTION = {
    "host": REDIS_SERVER,
    "port": REDIS_PORT,
    "db": REDIS_DB,
}
if REDIS_PASSWORD:
    CONSTANCE_REDIS_CONNECTION["password"] = REDIS_PASSWORD

CONSTANCE_CONFIG = {
    "FIRST_CLASS_PRICE": (35, "First class pack price"),
    "DISKSPACE_FREE_MAXMB": (10, "Max number of MB of storage for free plan"),
    "DISKSPACE_PAYED_MAXMB": (4000, "Max number of MB of storage for payed plan"),
    "SIGNUP_AUTHORIZED": (True, "Is Signup authorized ?"),
    "MAIL_ON_SUBSCRIBE": (False, "Mail managers when a new user subscribes?"),
    "BETA": (False, "Apply beta month bonus on First Class activation"),
    "BETA_MONTH_BONUS": (0, "Extra month balance when BETA is enabled"),
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
LANGUAGES = (("fr-fr", "French"),)
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DATE_INPUT_FORMATS = ("%Y-%m-%d", "%d/%m/%Y")
DATETIME_INPUT_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M:%S.%f",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
)

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "site-static"
STATICFILES_DIRS = [BASE_DIR / "cloudy" / "static"]
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
)
COMPRESS_URL = STATIC_URL

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": MEDIA_ROOT},
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Matches the single existing row in production's django_site (cloudy.fr).
SITE_ID = 1

INTERNAL_IPS = ["127.0.0.1"]

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "Cloudy <contact@cloudy.fr>")
EMAIL_SUBJECT_PREFIX = "CLOUDY - "
EMAIL_HOST = env("EMAIL_HOST", "")
EMAIL_PORT = int(env("EMAIL_PORT", "587") or "587")
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    (
        "django.core.mail.backends.smtp.EmailBackend"
        if EMAIL_HOST
        else "django.core.mail.backends.console.EmailBackend"
    ),
)

STRIPE_API_KEY = env("STRIPE_API_KEY", "")
STRIPE_FIRST_CLASS_SUBSCRIPTION = env("STRIPE_FIRST_CLASS_SUBSCRIPTION", "")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", "")

SNAPABUG_WIDGETID = env("SNAPABUG_WIDGETID", "")
GOOGLE_ANALYTICS_PROPERTY_ID = env("GOOGLE_ANALYTICS_PROPERTY_ID", "")
GAUGES_SITE_ID = env("GAUGES_SITE_ID", "")
# Staff user who receives manually uploaded logbooks. Empty disables that assignment.
IMPORT_DEFAULT_OWNER_EMAIL = env("IMPORT_DEFAULT_OWNER_EMAIL", "")

NOTICE_TYPE_IGNORE = ["empty_logbook", "sponsor_them"]

LOG_BOOKS_NAME_MAP = {
    "plane_dgac": "Avion DGAC",
    "plane_fcl1080": "FCL 1.080",
    "glider_dgac": "Planeur DGAC",
    "helicopter_dgac": "Hélico DGAC",
    "ulm_ffplum": "ULM",
    "balloon_dgac": "Ballon DGAC",
    "parachute_cloudy": "Parachute",
}
LOG_BOOKS_TYPE = tuple(LOG_BOOKS_NAME_MAP.keys())

try:
    from .local_settings import *  # ruff: ignore[undefined-local-with-import-star]
except ImportError:
    pass

# local_settings may override DEBUG. Wire the toolbar only after that, and only
# when DEBUG is still on — django-debug-toolbar is a dev dependency.
if DEBUG:
    INSTALLED_APPS.insert(INSTALLED_APPS.index("constance"), "debug_toolbar")
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")
