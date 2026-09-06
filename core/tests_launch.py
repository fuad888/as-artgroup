"""The pre-launch technical checklist, asserted rather than eyeballed."""

import re
from io import StringIO

from django.core.management import call_command
from django.test import override_settings

from core.models import SeoSettings
from core.testing import BaseTestCase

PAGES = ["/az/", "/ru/", "/az/haqqimizda/", "/az/layiheler/", "/az/elaqe/"]


class SeededTestCase(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_all", stdout=StringIO())


class MetaTagTests(SeededTestCase):
    def test_every_page_has_a_title_and_description(self):
        for path in PAGES:
            with self.subTest(path=path):
                html = self.client.get(path).content.decode()
                title = re.search(r"<title>(.*?)</title>", html, re.S)
                self.assertIsNotNone(title)
                self.assertGreater(len(title.group(1).strip()), 10)
                description = re.search(r'<meta name="description" content="(.*?)"', html, re.S)
                self.assertIsNotNone(description)
                self.assertGreater(len(description.group(1).strip()), 50)

    def test_every_page_declares_a_canonical_url(self):
        for path in PAGES:
            with self.subTest(path=path):
                html = self.client.get(path).content.decode()
                canonical = re.search(r'<link rel="canonical" href="(.*?)"', html)
                self.assertIsNotNone(canonical)
                self.assertTrue(canonical.group(1).startswith("http"))


class SocialPreviewTests(SeededTestCase):
    """A shared link with no og:image renders as a bare grey box."""

    def _og_image(self, path="/az/"):
        html = self.client.get(path).content.decode()
        found = re.search(r'<meta property="og:image" content="(.*?)"', html)
        self.assertIsNotNone(found, "og:image missing")
        return found.group(1)

    def test_pages_always_carry_a_preview_image(self):
        for path in PAGES:
            with self.subTest(path=path):
                self.assertTrue(self._og_image(path))

    def test_the_preview_image_url_is_absolute(self):
        """Facebook, WhatsApp and LinkedIn all reject a relative og:image."""
        self.assertRegex(self._og_image(), r"^https?://")

    def test_the_preview_image_file_is_actually_shipped(self):
        """Resolved through the finders, so this holds on a fresh clone too --
        collectstatic having been run is not part of the claim."""
        from django.contrib.staticfiles import finders

        self.assertIsNotNone(finders.find("img/og-default.png"))

    def test_dimensions_are_declared_so_the_crawler_need_not_guess(self):
        html = self.client.get("/az/").content.decode()
        self.assertIn('<meta property="og:image:width" content="1200">', html)
        self.assertIn('<meta property="og:image:height" content="630">', html)

    def test_twitter_card_shares_the_same_image(self):
        html = self.client.get("/az/").content.decode()
        twitter = re.search(r'<meta name="twitter:image" content="(.*?)"', html).group(1)
        self.assertEqual(twitter, self._og_image())


class FaviconTests(SeededTestCase):
    def test_the_root_favicon_request_is_answered(self):
        """Browsers ask for /favicon.ico whatever the markup says."""
        from django.contrib.staticfiles import finders

        response = self.client.get("/favicon.ico")
        self.assertIn(response.status_code, (301, 302))
        self.assertTrue(response["Location"].endswith(".ico"))
        self.assertIsNotNone(finders.find("favicon.ico"))

    def test_pages_link_an_icon_and_an_apple_touch_icon(self):
        html = self.client.get("/az/").content.decode()
        self.assertRegex(html, r'<link rel="icon" href="[^"]+\.ico"')
        self.assertRegex(html, r'<link rel="apple-touch-icon" href="[^"]+\.png"')


class ErrorPageTests(SeededTestCase):
    def test_the_404_page_is_the_site_and_not_djangos_default(self):
        response = self.client.get("/az/bele-sehife-yoxdur-12345/")
        self.assertEqual(response.status_code, 404)
        html = response.content.decode()
        self.assertIn("Belə səhifə tapılmadı", html)
        self.assertIn("topbar", html)  # the site chrome, so the visitor can navigate on

    def test_the_404_page_offers_a_way_back(self):
        html = self.client.get("/az/yoxdur/").content.decode()
        self.assertIn('href="/az/"', html)

    def test_the_500_page_needs_no_context(self):
        """Django renders 500.html with an empty context: no request, no
        context processors, no {% static %}. Anything else would 500 twice."""
        from django.template.loader import get_template

        rendered = get_template("500.html").render({})
        self.assertIn("AS-ART Group", rendered)
        self.assertNotIn("{{", rendered)
        self.assertNotIn("{%", rendered)


class IndexingTests(SeededTestCase):
    """allow_indexing gates both the robots meta and robots.txt. It ships off so
    a half-built site is never crawled; launch has to turn it on."""

    def _set_indexing(self, allowed):
        seo = SeoSettings.load()
        seo.allow_indexing = allowed
        seo.save()

    def test_indexing_off_blocks_both_channels(self):
        self._set_indexing(False)
        self.assertIn("noindex", self.client.get("/az/").content.decode())
        self.assertIn("Disallow: /", self.client.get("/robots.txt").content.decode())

    def test_indexing_on_clears_both_channels(self):
        self._set_indexing(True)
        html = self.client.get("/az/").content.decode()
        self.assertNotIn("noindex", html)
        robots = self.client.get("/robots.txt").content.decode()
        self.assertNotIn("Disallow: /\n", robots)
        self.assertIn("Sitemap:", robots)

    def test_the_sitemap_lists_both_languages_for_every_page(self):
        xml = self.client.get("/sitemap.xml").content.decode()
        self.assertGreaterEqual(xml.count("<url>"), 40)
        self.assertIn('hreflang="az"', xml)
        self.assertIn('hreflang="ru"', xml)


class PageWeightTests(SeededTestCase):
    """The hero is the largest contentful paint; it decides the mobile score."""

    def setUp(self):
        super().setUp()
        self.html = self.client.get("/az/").content.decode()
        self.hero = re.search(r'<div class="hero__bg">.*?</div>', self.html, re.S).group(0)

    def test_the_hero_offers_the_browser_a_phone_sized_variant(self):
        """One stored URL asks for w=2400 — 312 KB pushed at a 393 px screen."""
        srcset = re.search(r'srcset="(.*?)"', self.hero, re.S)
        self.assertIsNotNone(srcset, "hero has no srcset")
        widths = sorted(int(w) for w in re.findall(r"\s(\d+)w", srcset.group(1)))
        self.assertGreaterEqual(len(widths), 4)
        self.assertLessEqual(min(widths), 768)
        self.assertIn("sizes=", self.hero)

    def test_the_hero_is_fetched_eagerly_and_early(self):
        self.assertIn('fetchpriority="high"', self.hero)
        self.assertNotIn('loading="lazy"', self.hero)

    def test_below_the_fold_images_are_deferred(self):
        below_fold = self.html[self.html.index('id="layiheler"'):]
        images = re.findall(r"<img[^>]*>", below_fold)
        self.assertTrue(images)
        for tag in images:
            with self.subTest(tag=tag[:70]):
                self.assertIn('loading="lazy"', tag)

    def test_the_map_iframe_does_not_block_the_page(self):
        self.assertRegex(
            re.search(r"<iframe[^>]*maps[^>]*>", self.html, re.S).group(0), r'loading="lazy"'
        )

    def test_a_non_resizable_url_gets_no_srcset(self):
        """An uploaded file has no resizing service behind it; inventing widths
        there would produce broken URLs."""
        from core.templatetags.images import responsive_srcset

        self.assertEqual(responsive_srcset("/media/seo/upload.png"), "")
        self.assertEqual(responsive_srcset(""), "")
        self.assertIn("480w", responsive_srcset("https://images.unsplash.com/photo-1?w=2400"))


class IndexingDeployCheckTests(BaseTestCase):
    """The indexing switch lives in the database, so Django's own --deploy
    checks cannot see it. This one makes a silent misconfiguration loud."""

    def _run(self):
        from core.checks import indexing_should_be_on_in_production

        return indexing_should_be_on_in_production(None)

    def _set_indexing(self, allowed):
        seo = SeoSettings.load()
        seo.allow_indexing = allowed
        seo.save()

    @override_settings(DEBUG=False)
    def test_it_warns_when_a_live_site_is_not_indexable(self):
        self._set_indexing(False)
        warnings = self._run()
        self.assertEqual([w.id for w in warnings], ["core.W001"])
        self.assertIn("seosettings", warnings[0].hint)

    @override_settings(DEBUG=False)
    def test_it_stays_quiet_once_indexing_is_on(self):
        self._set_indexing(True)
        self.assertEqual(self._run(), [])

    @override_settings(DEBUG=True)
    def test_it_says_nothing_during_local_development(self):
        self._set_indexing(False)
        self.assertEqual(self._run(), [])


class ErrorVisibilityTests(BaseTestCase):
    """A 500 on shared hosting is only fixable if its traceback is readable."""

    def test_request_errors_are_written_to_a_file_not_just_stderr(self):
        from django.conf import settings

        handlers = settings.LOGGING["loggers"]["django.request"]["handlers"]
        self.assertIn("error_file", handlers)
        handler = settings.LOGGING["handlers"]["error_file"]
        self.assertEqual(handler["level"], "ERROR")
        self.assertTrue(handler["filename"].endswith("django-error.log"))

    def test_the_error_log_rotates_so_it_cannot_fill_the_disk(self):
        from django.conf import settings

        handler = settings.LOGGING["handlers"]["error_file"]
        self.assertEqual(handler["class"], "logging.handlers.RotatingFileHandler")
        self.assertGreater(handler["maxBytes"], 0)
        self.assertGreater(handler["backupCount"], 0)

    def test_an_exception_reaches_the_log_with_its_traceback(self):
        import logging
        from pathlib import Path

        from django.conf import settings

        path = Path(settings.LOGGING["handlers"]["error_file"]["filename"])
        before = path.stat().st_size if path.exists() else 0
        try:
            raise ValueError("probe-for-the-log")
        except ValueError:
            logging.getLogger("django.request").exception("probe")
        written = path.read_text()[before:]
        self.assertIn("probe-for-the-log", written)
        self.assertIn("Traceback", written)
