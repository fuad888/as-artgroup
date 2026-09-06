"""The admin returned 500 in production while every test passed.

The suite swaps in plain static storage so it need not depend on collectstatic,
and that is exactly what hid the bug: under the manifest storage a third-party
template asked for a path with no manifest entry and the strict storage raised.
These tests cover the manifest path specifically.
"""

from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings

from core.storage import ResilientManifestStaticFilesStorage
from core.testing import BaseTestCase

MANIFEST_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "core.storage.ResilientManifestStaticFilesStorage"},
}

MANIFEST_FILE = Path(settings.STATIC_ROOT) / "staticfiles.json"


class StorageFallbackTests(BaseTestCase):
    """Fast: no collectstatic needed, the manifest is supplied by hand."""

    def _storage(self, manifest):
        storage = ResilientManifestStaticFilesStorage()
        storage.hashed_files = dict(manifest)
        return storage

    def test_an_unknown_path_falls_back_instead_of_raising(self):
        """django-jazzmin renders {% static 'vendor/bootswatch' %} — a directory,
        so it can build theme URLs in JavaScript. Strict storage answered that
        with a ValueError and took every admin page down with it."""
        storage = self._storage({})
        self.assertEqual(storage.stored_name("vendor/bootswatch"), "vendor/bootswatch")

    def test_the_fallback_is_logged_so_a_real_typo_stays_visible(self):
        storage = self._storage({})
        with self.assertLogs("core.storage", level="WARNING") as captured:
            storage.stored_name("css/does-not-exist.css")
        self.assertIn("css/does-not-exist.css", captured.output[0])

    def test_known_files_still_get_their_hashed_name(self):
        storage = self._storage({"css/site.css": "css/site.abc123.css"})
        self.assertEqual(storage.stored_name("css/site.css"), "css/site.abc123.css")

    def test_production_uses_the_resilient_backend(self):
        """Checked against the production constant, not the live setting: the
        suite deliberately swaps STORAGES for plain storage, and reading the
        swapped value is what let this bug ship green."""
        self.assertEqual(
            settings.PRODUCTION_STATICFILES_BACKEND,
            "core.storage.ResilientManifestStaticFilesStorage",
        )


@override_settings(STORAGES=MANIFEST_STORAGE)
class AdminUnderManifestStorageTests(BaseTestCase):
    """The real thing, against a built manifest. Deploys run collectstatic, so
    this is the configuration production actually serves."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not MANIFEST_FILE.exists():
            raise cls.skipException(
                f"{MANIFEST_FILE} missing — run `manage.py collectstatic` to cover "
                "the storage the site actually deploys with"
            )

    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_superuser(
            username="manifest-probe", email="p@example.com", password="Xq7!vm2Zt9"
        )

    def test_the_admin_dashboard_renders(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_the_admin_login_page_renders(self):
        self.assertEqual(self.client.get("/admin/login/").status_code, 200)

    def test_a_model_admin_page_renders(self):
        self.client.force_login(self.user)
        response = self.client.get("/admin/core/seosettings/", follow=True)
        self.assertEqual(response.status_code, 200)

    def test_the_public_site_renders(self):
        self.assertEqual(self.client.get("/az/").status_code, 200)
