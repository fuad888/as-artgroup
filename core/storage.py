import logging

from whitenoise.storage import CompressedManifestStaticFilesStorage

logger = logging.getLogger(__name__)


class ResilientManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """Hashed and pre-compressed static files, but a missing manifest entry
    must not take the site down.

    django-jazzmin's admin/base.html renders
    ``data-theme-base="{% static 'vendor/bootswatch' %}"`` — a *directory*, so
    its JavaScript can build theme URLs itself. There is no manifest entry for a
    directory, and the strict storage answers that with a ValueError, so every
    page extending the admin base template returned a 500 while the login page
    (a different template) kept working.

    A third-party template should not be able to do that. Unknown names fall
    back to the unhashed path — which is what jazzmin wants anyway — and are
    logged, so a genuine typo is still visible instead of silently ignored.
    """

    manifest_strict = False

    def stored_name(self, name):
        try:
            return super().stored_name(name)
        except ValueError:
            logger.warning("Static path not in the manifest, serving unhashed: %s", name)
            return name
