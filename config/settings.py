"""
Django settings for EV House Management.

Valori sensibili letti da variabili d'ambiente con fallback per lo sviluppo.
In produzione impostare almeno: DJANGO_SECRET_KEY, DJANGO_DEBUG=False,
DJANGO_ALLOWED_HOSTS.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default):
    raw = os.environ.get(name)
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


# SECURITY WARNING: chiave di default solo per sviluppo, cambiare in produzione.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-ev-house-management-dev-key-change-me-in-production",
)

DEBUG = env_bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["*"])

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", [])


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    # App locali
    "core",
    "properties",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "it-it"
TIME_ZONE = "Europe/Zurich"
USE_I18N = True
USE_TZ = True


# File statici e media
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Email: in sviluppo scrive in console. In produzione configurare SMTP.
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@evhousemanagement.com")
CONTACT_RECIPIENT_EMAIL = os.environ.get("CONTACT_RECIPIENT_EMAIL", "evhouse92@gmail.com")


# Dati usati nei template (footer, SEO, JSON-LD)
SITE_NAME = os.environ.get("SITE_NAME", "EV House Management")
SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "www.evhousemanagement.com")
COMPANY_LEGAL_NAME = os.environ.get("COMPANY_LEGAL_NAME", "EV House Management")
COMPANY_VAT = os.environ.get("COMPANY_VAT", "01634110918")
COMPANY_ADDRESS = os.environ.get("COMPANY_ADDRESS", "Sardegna, Italia")  # TODO: indirizzo completo
COMPANY_EMAIL = os.environ.get("COMPANY_EMAIL", "evhouse92@gmail.com")
COMPANY_PHONE = os.environ.get("COMPANY_PHONE", "")  # TODO: telefono pubblico


# Sicurezza aggiuntiva quando DEBUG=False
if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
