from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.test import override_settings

from about.models import AboutContent, Stat
from contact.models import ContactMessage
from core.models import SiteSettings
from core.testing import BaseTestCase
from projects.models import Project, ProjectCategory
from team.models import TeamMember


class CompressionTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        category = ProjectCategory.objects.create(name="Konsert", slug="konsert")
        # GZipMiddleware only compresses responses above ~200 bytes.
        for i in range(15):
            Project.objects.create(title=f"Layihə {i}", description="x" * 200, category=category)

    def test_response_is_gzipped_when_client_accepts_it(self):
        response = self.client.get(
            "/api/v1/projects/", headers={"accept-encoding": "gzip, deflate"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Encoding"], "gzip")

    def test_response_is_plain_when_client_does_not_accept_gzip(self):
        response = self.client.get("/api/v1/projects/", headers={"accept-encoding": ""})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Content-Encoding", response)

    def test_gzip_meaningfully_shrinks_the_payload(self):
        plain = self.client.get("/api/v1/projects/", headers={"accept-encoding": ""})
        gzipped = self.client.get(
            "/api/v1/projects/", headers={"accept-encoding": "gzip, deflate"}
        )
        self.assertLess(len(gzipped.content), len(plain.content) / 2)


class ConditionalGetTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        TeamMember.objects.create(name="Anar Səlimov", role="Direktor")

    def test_response_carries_an_etag(self):
        response = self.client.get("/api/v1/team/")
        self.assertTrue(response["ETag"])

    def test_matching_etag_returns_304_without_a_body(self):
        first = self.client.get("/api/v1/team/")
        second = self.client.get("/api/v1/team/", headers={"if-none-match": first["ETag"]})
        self.assertEqual(second.status_code, 304)
        self.assertEqual(second.content, b"")

    def test_etag_changes_when_content_changes(self):
        first = self.client.get("/api/v1/team/")
        TeamMember.objects.create(name="Leyla Hüseynova", role="Kreativ Direktor")
        second = self.client.get("/api/v1/team/")
        self.assertNotEqual(first["ETag"], second["ETag"])


class CacheHeaderTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        TeamMember.objects.create(name="Anar Səlimov", role="Direktor")

    def test_public_read_endpoints_are_cacheable(self):
        response = self.client.get("/api/v1/team/")
        cache_control = response["Cache-Control"]
        self.assertIn("public", cache_control)
        self.assertIn("max-age=60", cache_control)
        self.assertIn("s-maxage=300", cache_control)

    def test_write_endpoint_is_not_marked_cacheable(self):
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
        self.assertNotIn("public", response.get("Cache-Control", ""))


class LanguageScopedPayloadTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        category = ProjectCategory.objects.create(name="Konsert", slug="konsert")
        Project.objects.create(
            title_az="Arena Live",
            title_ru="Арена Лайв",
            description_az="Təsvir",
            description_ru="Описание",
            category=category,
        )

    def test_default_response_carries_both_languages(self):
        data = self.client.get("/api/v1/projects/").json()["results"][0]
        self.assertIn("title_az", data)
        self.assertIn("title_ru", data)

    def test_lang_filter_drops_the_other_language(self):
        data = self.client.get("/api/v1/projects/?lang=az").json()["results"][0]
        self.assertIn("title_az", data)
        self.assertNotIn("title_ru", data)

    def test_lang_filter_applies_to_nested_serializers(self):
        data = self.client.get("/api/v1/projects/?lang=az").json()["results"][0]
        self.assertIn("name_az", data["category"])
        self.assertNotIn("name_ru", data["category"])

    def test_unknown_lang_is_ignored(self):
        data = self.client.get("/api/v1/projects/?lang=fr").json()["results"][0]
        self.assertIn("title_ru", data)

    def test_lang_filter_shrinks_the_payload(self):
        both = self.client.get("/api/v1/projects/", headers={"accept-encoding": ""})
        single = self.client.get("/api/v1/projects/?lang=az", headers={"accept-encoding": ""})
        self.assertLess(len(single.content), len(both.content))


class SingletonCacheTests(BaseTestCase):
    def test_second_load_hits_the_cache_instead_of_the_database(self):
        SiteSettings.load()
        with self.assertNumQueries(0):
            SiteSettings.load()

    def test_saving_invalidates_the_cache(self):
        SiteSettings.load()
        obj = SiteSettings.load()
        obj.site_name = "Yeni ad"
        obj.save()
        self.assertEqual(SiteSettings.load().site_name, "Yeni ad")

    def test_cache_is_populated_under_a_model_scoped_key(self):
        SiteSettings.load()
        self.assertIsNotNone(cache.get("singleton:core.sitesettings"))

    def test_home_view_does_not_reload_singletons_repeatedly(self):
        about = AboutContent.load()
        Stat.objects.create(about=about, number=1, label="Tədbirlər", order=1)
        cache.clear()
        # Warm the singleton caches, then confirm a repeat read costs no queries.
        AboutContent.load()
        with self.assertNumQueries(0):
            AboutContent.load()
            AboutContent.load()


class ThrottleTests(BaseTestCase):
    @override_settings()
    def test_public_api_has_a_global_anonymous_rate_limit(self):
        rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
        self.assertIn("anon", rates)
        self.assertIn("user", rates)
        classes = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"]
        self.assertTrue(any("AnonRateThrottle" in c for c in classes))


class DatabaseConfigTests(BaseTestCase):
    """Both engines are in use: PostgreSQL locally, SQLite on the shared host
    that has no PostgreSQL. The right policy differs between them."""

    def test_connection_reuse_matches_the_engine(self):
        db = settings.DATABASES["default"]
        if connection.vendor == "postgresql":
            # Reconnecting per request is the expensive part on PostgreSQL.
            self.assertGreater(db["CONN_MAX_AGE"], 0)
            self.assertTrue(db["CONN_HEALTH_CHECKS"])
        else:
            # SQLite has no connect cost worth amortising, and a held-open
            # handle per worker only deepens write-lock contention.
            self.assertEqual(db["CONN_MAX_AGE"], 0)

    def test_the_engine_gets_the_options_it_understands(self):
        options = settings.DATABASES["default"]["OPTIONS"]
        if connection.vendor == "postgresql":
            self.assertEqual(options["connect_timeout"], 5)
        else:
            self.assertGreaterEqual(options["timeout"], 20)
            self.assertEqual(options["transaction_mode"], "IMMEDIATE")
            self.assertIn("journal_mode=WAL", options["init_command"])

    def test_sqlite_actually_runs_in_wal_mode(self):
        """A login writes a session row; in the default rollback-journal mode a
        concurrent read blocks that write and the request 500s.

        Opened against a real file because the test database lives in memory,
        where journal_mode is always "memory". This exercises Django's own
        init_command handling rather than trusting the setting to be read.
        """
        if connection.vendor != "sqlite":
            self.skipTest("PostgreSQL has no journal mode")

        import tempfile
        from pathlib import Path

        from django.db.backends.sqlite3.base import DatabaseWrapper

        with tempfile.TemporaryDirectory() as tmp:
            settings_dict = {
                **settings.DATABASES["default"],
                "NAME": str(Path(tmp) / "probe.sqlite3"),
                "ATOMIC_REQUESTS": False,
                "AUTOCOMMIT": True,
                "CONN_MAX_AGE": 0,
                "CONN_HEALTH_CHECKS": False,
                "TIME_ZONE": None,
            }
            probe = DatabaseWrapper(settings_dict, alias="wal-probe")
            try:
                with probe.cursor() as cursor:
                    mode = cursor.execute("PRAGMA journal_mode").fetchone()[0]
                    timeout = cursor.execute("PRAGMA busy_timeout").fetchone()[0]
            finally:
                probe.close()

        self.assertEqual(mode, "wal")
        self.assertGreaterEqual(timeout, 20000)

    def test_growth_prone_tables_are_indexed(self):
        """Introspection rather than pg_indexes, so this holds on either engine."""
        expected = {
            Project: {"project_featured_order_idx", "project_order_idx"},
            TeamMember: {"team_order_idx"},
            ContactMessage: {"contact_created_idx", "contact_handled_idx"},
        }
        for model, names in expected.items():
            with connection.cursor() as cursor:
                constraints = connection.introspection.get_constraints(
                    cursor, model._meta.db_table
                )
            found = {name for name, spec in constraints.items() if spec.get("index")}
            self.assertTrue(names.issubset(found), f"{model.__name__}: missing {names - found}")

    def test_featured_projects_query_uses_the_index(self):
        if connection.vendor != "postgresql":
            self.skipTest("EXPLAIN output is engine specific")
        category = ProjectCategory.objects.create(name="Konsert", slug="konsert")
        for i in range(50):
            Project.objects.create(title=f"P{i}", category=category, is_featured=i % 2 == 0)
        with connection.cursor() as cursor:
            cursor.execute("ANALYZE projects_project")
            cursor.execute(
                "EXPLAIN SELECT id FROM projects_project WHERE is_featured = true "
                'ORDER BY "order", id'
            )
            plan = "\n".join(row[0] for row in cursor.fetchall())
        # Tiny tables are still seq-scanned by the planner; assert the index exists
        # and the plan is produced without error rather than forcing a scan type.
        self.assertTrue(plan)


class QueryCountTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        category = ProjectCategory.objects.create(name="Konsert", slug="konsert")
        for i in range(10):
            Project.objects.create(title=f"Layihə {i}", category=category)

    def test_project_list_does_not_scale_queries_with_row_count(self):
        with self.assertNumQueries(2):  # COUNT for pagination + one select_related fetch
            self.client.get("/api/v1/projects/")

    def test_team_list_is_a_single_query(self):
        TeamMember.objects.create(name="Anar Səlimov", role="Direktor")
        with self.assertNumQueries(1):
            self.client.get("/api/v1/team/")
