"""
Django settings for the AS-ART Group project.
"""

import sys
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])


# Application definition

INSTALLED_APPS = [
    # Must load before django.contrib.admin
    "jazzmin",
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    # Third-party
    "rest_framework",
    "corsheaders",
    "django_filters",
    # Project apps — each app is its own page/section (models, admin, views, api)
    "core",
    "home",
    "about",
    "equipment",
    "projects",
    "team",
    "contact",
    "ai_integrations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # GZip must wrap the response before anything else reads its body. Safe against
    # BREACH here because Django masks CSRF tokens per-request.
    "django.middleware.gzip.GZipMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    # Emits ETag / handles If-None-Match so unchanged pages return 304.
    "django.middleware.http.ConditionalGetMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Last in the list, so it runs first on the way out and can see the
    # finished response before anything else inspects its headers.
    "core.middleware.HtmlCacheControlMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "core.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# PostgreSQL in production; SQLite is also supported (e.g. while a host's
# Postgres isn't provisioned yet) — connect_timeout is Postgres-only.

DATABASES = {
    "default": {
        **env.db("DATABASE_URL"),
        # Persistent connections: without this Django opens a brand new
        # PostgreSQL connection for every single request.
        "CONN_MAX_AGE": env.int("DATABASE_CONN_MAX_AGE", default=60),
        # Guards against handing a request a connection the server already closed.
        "CONN_HEALTH_CHECKS": True,
    },
}
_db_engine = DATABASES["default"]["ENGINE"]
if "postgresql" in _db_engine:
    DATABASES["default"]["OPTIONS"] = {"connect_timeout": 5}
elif "sqlite" in _db_engine:
    # SQLite serialises writes, and a web app writes on every login (session
    # row + last_login). Under two workers the default settings raise
    # "database is locked" on exactly those requests: reads keep working, the
    # login 500s. WAL lets readers continue during a write, the longer timeout
    # waits for the lock instead of giving up, and IMMEDIATE takes the write
    # lock up front so two workers cannot deadlock upgrading a read.
    DATABASES["default"]["OPTIONS"] = {
        "timeout": 20,
        "transaction_mode": "IMMEDIATE",
        "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;",
    }
    # Holding the file open per worker makes contention worse, and SQLite has
    # no connection cost worth amortising.
    DATABASES["default"]["CONN_MAX_AGE"] = 0


# Cache — Redis when REDIS_URL is configured, in-memory otherwise.
# This matters beyond speed: DRF throttle counters live in the cache, so with the
# per-process LocMemCache every worker would enforce its own separate limit.

REDIS_URL = env("REDIS_URL", default="")

if REDIS_URL:
    CACHES = {
        "default": {
            # Degrades to a cache miss instead of raising when Redis is down.
            "BACKEND": "core.cache.ResilientRedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {"socket_connect_timeout": 3, "socket_timeout": 3},
            "KEY_PREFIX": "asart",
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "asart-locmem",
        }
    }

CACHE_TTL_SETTINGS = env.int("CACHE_TTL_SETTINGS", default=300)


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization — Azerbaijani (default) + Russian

LANGUAGE_CODE = "az"

LANGUAGES = [
    ("az", "Azərbaycan"),
    ("ru", "Русский"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

TIME_ZONE = "Asia/Baku"
USE_I18N = True
USE_TZ = True

MODELTRANSLATION_DEFAULT_LANGUAGE = "az"
MODELTRANSLATION_LANGUAGES = ("az", "ru")


# Static / media files

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# WhiteNoise serves collected static files with hashed names, pre-compressed as
# gzip + brotli, so they can be cached immutably for a year.
# Named separately because the test block below swaps STORAGES out; this stays
# readable as the backend production actually serves with.
PRODUCTION_STATICFILES_BACKEND = "core.storage.ResilientManifestStaticFilesStorage"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": PRODUCTION_STATICFILES_BACKEND},
}
WHITENOISE_MAX_AGE = 31536000

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST Framework — real, working API so future consumers (future
# frontend, mobile app, or an AI agent) can already pull site content.

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("THROTTLE_ANON", default="120/min"),
        "user": env("THROTTLE_USER", default="600/min"),
        "contact": env("THROTTLE_CONTACT", default="5/hour"),
    },
}

# CORS — no origins allowed by default until a frontend/AI consumer needs it.
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])


# Email — contact form notifications.
# Without EMAIL_HOST the console backend prints messages to the terminal, so the
# flow is testable before real SMTP credentials exist.

EMAIL_HOST = env("EMAIL_HOST", default="")

if EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
    EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Keeps a dead SMTP server from stalling the contact form response.
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=5)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="AS-ART Group <noreply@as-artgroup.az>")

# Where contact submissions are sent. Empty falls back to SiteSettings.email.
CONTACT_NOTIFY_EMAIL = env("CONTACT_NOTIFY_EMAIL", default="")


# AI readiness — reserved env slots only, nothing reads these yet.
AI_OPENAI_API_KEY = env("AI_OPENAI_API_KEY", default="")
AI_ANTHROPIC_API_KEY = env("AI_ANTHROPIC_API_KEY", default="")


# On shared hosting stderr disappears into a log the panel may not surface, so
# unhandled exceptions also go to a file inside the project that is readable
# over SSH or the file manager. If the directory cannot be created (read-only
# deploy), logging quietly falls back to the console alone.
_LOG_DIR = BASE_DIR / "logs"
_error_handlers = ["console"]
_file_handler = {}
try:
    _LOG_DIR.mkdir(exist_ok=True)
    _file_handler = {
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(_LOG_DIR / "django-error.log"),
            "maxBytes": 2 * 1024 * 1024,
            "backupCount": 3,
            "level": "ERROR",
            "formatter": "verbose",
        }
    }
    _error_handlers.append("error_file")
except OSError:
    pass

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        **_file_handler,
    },
    "root": {"handlers": _error_handlers, "level": "WARNING"},
    "loggers": {
        # The traceback behind any 500 lands here.
        "django.request": {"handlers": _error_handlers, "level": "ERROR", "propagate": False},
        "contact": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "core.cache": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}


# Production hardening — only applies once DEBUG is off.

if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])


# django-jazzmin admin theme

JAZZMIN_SETTINGS = {
    "site_title": "AS-ART Group Admin",
    "site_header": "AS-ART Group",
    "site_brand": "AS-ART Group",
    "welcome_sign": "AS-ART Group idarəetmə paneli",
    "copyright": "AS-ART Group",
    "show_ui_builder": False,
    "order_with_respect_to": [
        "core",
        "home",
        "about",
        "equipment",
        "projects",
        "team",
        "contact",
        "ai_integrations",
        "auth",
    ],
    "icons": {
        "core.SiteSettings": "fas fa-cog",
        "core.ServiceTag": "fas fa-tags",
        "home.HeroContent": "fas fa-star",
        "about.AboutContent": "fas fa-circle-info",
        "equipment.EquipmentCategory": "fas fa-lightbulb",
        "projects.Project": "fas fa-photo-film",
        "projects.ProjectCategory": "fas fa-folder",
        "team.TeamMember": "fas fa-users",
        "contact.ContactMessage": "fas fa-envelope",
        "ai_integrations.AIFeatureFlag": "fas fa-robot",
        "auth.User": "fas fa-user",
        "auth.Group": "fas fa-users-gear",
    },
}
JAZZMIN_UI_TWEAKS = {
    "theme": "darkly",
}


# Tests get their own in-process cache so they never read, write or flush the
# Redis instance the running site is using.
if "test" in sys.argv:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "asart-tests",
        }
    }
    # Plain storage so the suite doesn't depend on collectstatic having been run.
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
