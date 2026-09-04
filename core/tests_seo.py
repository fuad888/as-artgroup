import json

from django.template import Context, Template
from django.test import RequestFactory, TestCase, override_settings

from core.testing import BaseTestCase

from core.models import SeoSettings, SiteSettings
from projects.models import Project, ProjectCategory
from team.models import TeamMember


class RobotsTxtTests(BaseTestCase):
    def test_blocks_everything_while_indexing_is_off(self):
        seo = SeoSettings.load()
        seo.allow_indexing = False
        seo.save()

        response = self.client.get("/robots.txt")
        body = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertIn("Disallow: /", body)
        self.assertNotIn("Sitemap:", body)

    def test_allows_crawling_and_advertises_sitemap_once_enabled(self):
        seo = SeoSettings.load()
        seo.allow_indexing = True
        seo.save()

        body = self.client.get("/robots.txt").content.decode()
        self.assertIn("Disallow: /admin/", body)
        self.assertIn("Disallow: /api/", body)
        self.assertIn("Sitemap: http://testserver/sitemap.xml", body)


class SitemapTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        category = ProjectCategory.objects.create(name="Konsert", slug="konsert")
        Project.objects.create(title="Arena Live", category=category)
        TeamMember.objects.create(name="Anar Səlimov", role="Direktor")

    def test_sitemap_renders_both_languages(self):
        response = self.client.get("/sitemap.xml")
        body = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn("/az/layiheler/arena-live/", body)
        self.assertIn("/ru/layiheler/arena-live/", body)

    def test_sitemap_includes_static_pages_and_team(self):
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertIn("/az/haqqimizda/", body)
        self.assertIn("/az/komanda/anar-selimov/", body)

    def test_sitemap_declares_hreflang_alternates(self):
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertIn('hreflang="ru"', body)
        self.assertIn('hreflang="az"', body)


class SeoFallbackTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.category = ProjectCategory.objects.create(name="Konsert", slug="konsert")

    def test_project_falls_back_to_title_and_description(self):
        project = Project.objects.create(
            title="Arena Live", description="x" * 300, category=self.category
        )
        self.assertEqual(project.seo_title, "Arena Live")
        self.assertEqual(len(project.seo_description), 160)

    def test_project_override_wins(self):
        project = Project.objects.create(
            title="Arena Live",
            meta_title="Özəl SEO başlığı",
            meta_description="Özəl təsvir",
            category=self.category,
        )
        self.assertEqual(project.seo_title, "Özəl SEO başlığı")
        self.assertEqual(project.seo_description, "Özəl təsvir")

    def test_team_member_falls_back_to_name_and_role(self):
        member = TeamMember.objects.create(name="Anar Səlimov", role="Direktor")
        self.assertEqual(member.seo_title, "Anar Səlimov — Direktor")


class SeoTemplateTagTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        site_settings = SiteSettings.load()
        site_settings.site_name = "AS-ART Group"
        site_settings.meta_description_az = "Tam dövrlü prodakşn"
        site_settings.instagram_url = "https://instagram.com/asart"
        site_settings.phone = "+994 12 000 00 00"
        site_settings.address_line_az = "Nizami küç. 203"
        site_settings.save()

    def _render(self, template_string, **extra):
        request = self.factory.get("/az/layiheler/")
        context = {
            "request": request,
            "site_settings": SiteSettings.load(),
            "seo_settings": SeoSettings.load(),
            **extra,
        }
        return Template(template_string).render(Context(context))

    def test_alternate_url_swaps_language_prefix(self):
        output = self._render("{% load seo %}{% alternate_url 'ru' %}")
        self.assertEqual(output.strip(), "/ru/layiheler/")

    def test_canonical_url_is_absolute(self):
        output = self._render("{% load seo %}{% canonical_url %}")
        self.assertEqual(output.strip(), "http://testserver/az/layiheler/")

    def test_organization_schema_is_valid_json(self):
        output = self._render("{% load seo %}{% organization_schema %}")
        data = json.loads(output)
        self.assertEqual(data["@type"], "Organization")
        self.assertEqual(data["name"], "AS-ART Group")
        self.assertIn("https://instagram.com/asart", data["sameAs"])
        self.assertEqual(data["address"]["streetAddress"], "Nizami küç. 203")

    def test_organization_schema_escapes_script_breakouts(self):
        site_settings = SiteSettings.load()
        site_settings.site_name = "</script><script>alert(1)</script>"
        site_settings.save()
        output = self._render("{% load seo %}{% organization_schema %}")
        self.assertNotIn("</script>", output)
        self.assertIn("\\u003C", output)


class SeoMetaIncludeTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        SiteSettings.load()

    def _render(self, **extra):
        request = self.factory.get("/az/")
        context = {
            "request": request,
            "site_settings": SiteSettings.load(),
            "seo_settings": SeoSettings.load(),
            "LANGUAGES": [("az", "Azərbaycan"), ("ru", "Русский")],
            "LANGUAGE_CODE": "az",
            **extra,
        }
        return Template('{% include "includes/seo_meta.html" %}').render(Context(context))

    def test_emits_noindex_while_indexing_is_off(self):
        self.assertIn('name="robots" content="noindex, nofollow"', self._render())

    def test_drops_noindex_once_indexing_is_enabled(self):
        seo = SeoSettings.load()
        seo.allow_indexing = True
        seo.save()
        self.assertNotIn("noindex", self._render())

    def test_uses_per_page_seo_context(self):
        output = self._render(seo_title="Layihələr", seo_description="Keçirdiyimiz şoular")
        self.assertIn("<title>Layihələr | AS-ART Group</title>", output)
        self.assertIn('content="Keçirdiyimiz şoular"', output)

    def test_emits_hreflang_for_both_languages(self):
        output = self._render()
        self.assertIn('hreflang="az"', output)
        self.assertIn('hreflang="ru"', output)
        self.assertIn('hreflang="x-default"', output)


class AnalyticsIncludeTests(BaseTestCase):
    def _render(self, analytics_enabled=True):
        return Template('{% include "includes/analytics.html" %}').render(
            Context(
                {
                    "seo_settings": SeoSettings.load(),
                    "analytics_enabled": analytics_enabled,
                }
            )
        )

    def test_renders_nothing_without_an_id(self):
        self.assertNotIn("googletagmanager", self._render())

    def test_renders_ga4_snippet_when_configured(self):
        seo = SeoSettings.load()
        seo.google_analytics_id = "G-ABCD123456"
        seo.save()
        output = self._render()
        self.assertIn("gtag/js?id=G-ABCD123456", output)
        self.assertIn("gtag('config', 'G-ABCD123456')", output)

    def test_is_suppressed_while_analytics_disabled(self):
        seo = SeoSettings.load()
        seo.google_analytics_id = "G-ABCD123456"
        seo.save()
        self.assertNotIn("googletagmanager", self._render(analytics_enabled=False))

    @override_settings(DEBUG=True)
    def test_context_processor_disables_analytics_in_debug(self):
        from core.context_processors import site

        self.assertFalse(site(None)["analytics_enabled"])

    @override_settings(DEBUG=False)
    def test_context_processor_enables_analytics_in_production(self):
        from core.context_processors import site

        self.assertTrue(site(None)["analytics_enabled"])


class SeoSettingsValidationTests(BaseTestCase):
    def test_rejects_malformed_ga4_id(self):
        from django.core.exceptions import ValidationError

        seo = SeoSettings.load()
        seo.google_analytics_id = "UA-12345-1"
        with self.assertRaises(ValidationError):
            seo.full_clean()

    def test_accepts_valid_ga4_id(self):
        seo = SeoSettings.load()
        seo.google_analytics_id = "G-ABCD123456"
        seo.full_clean()
