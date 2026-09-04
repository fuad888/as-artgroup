from django.core.cache import caches
from django.test import override_settings

from core.models import SiteSettings
from core.testing import BaseTestCase
from projects.models import Project, ProjectCategory
from team.models import TeamMember

# Port 1 is closed, so every Redis call fails fast — a stand-in for "Redis is down".
BROKEN_REDIS = {
    "default": {
        "BACKEND": "core.cache.ResilientRedisCache",
        "LOCATION": "redis://127.0.0.1:1/0",
        "OPTIONS": {"socket_connect_timeout": 0.05, "socket_timeout": 0.05},
    }
}


@override_settings(CACHES=BROKEN_REDIS)
class CacheOutageTests(BaseTestCase):
    """Everything here runs against an unreachable Redis."""

    def setUp(self):
        # Skip BaseTestCase.setUp's cache.clear() — it would target broken Redis.
        caches.close_all()

    def test_cache_operations_degrade_instead_of_raising(self):
        cache = caches["default"]
        self.assertIsNone(cache.get("missing"))
        self.assertEqual(cache.get("missing", "fallback"), "fallback")
        self.assertIsNone(cache.set("k", "v"))
        self.assertFalse(cache.add("k", "v"))
        self.assertFalse(cache.delete("k"))
        self.assertFalse(cache.has_key("k"))
        self.assertEqual(cache.get_many(["a", "b"]), {})
        self.assertEqual(cache.set_many({"a": 1}), ["a"])
        self.assertIsNone(cache.delete_many(["a"]))
        self.assertFalse(cache.touch("k"))
        self.assertIsNone(cache.clear())

    def test_singleton_still_loads_from_the_database(self):
        settings_obj = SiteSettings.load()
        self.assertEqual(settings_obj.pk, 1)
        self.assertEqual(SiteSettings.objects.count(), 1)

    def test_singleton_save_still_works(self):
        settings_obj = SiteSettings.load()
        settings_obj.site_name = "Redis olmadan"
        settings_obj.save()
        self.assertEqual(SiteSettings.objects.get(pk=1).site_name, "Redis olmadan")

    def test_public_api_still_serves_content(self):
        category = ProjectCategory.objects.create(name="Konsert", slug="konsert")
        Project.objects.create(title="Arena Live", category=category)
        TeamMember.objects.create(name="Anar Səlimov", role="Direktor")

        for path in ["/api/v1/", "/api/v1/projects/", "/api/v1/team/", "/api/v1/core/site-settings/"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_throttled_endpoint_fails_open_rather_than_erroring(self):
        response = self.client.post(
            "/api/v1/contact/messages/",
            {
                "name": "Test",
                "email": "t@example.com",
                "phone": "+994 50 123 45 67",
                "message": "salam",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

    def test_sitemap_and_robots_still_render(self):
        self.assertEqual(self.client.get("/sitemap.xml").status_code, 200)
        self.assertEqual(self.client.get("/robots.txt").status_code, 200)


class CacheRecoveryTests(BaseTestCase):
    def test_caching_resumes_once_redis_is_reachable_again(self):
        with override_settings(CACHES=BROKEN_REDIS):
            caches.close_all()
            SiteSettings.load()  # served straight from the database

        # Back on the working (in-process, test) cache the value is cached again.
        caches.close_all()
        SiteSettings.load()
        with self.assertNumQueries(0):
            SiteSettings.load()
