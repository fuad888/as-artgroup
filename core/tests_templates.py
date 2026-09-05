import re
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import override_settings
from io import StringIO

from core.testing import BaseTestCase

ORIGINAL_HTML = Path(settings.BASE_DIR) / "index.html"


def body(html):
    match = re.search(r"<body[^>]*>(.*)</body>", html, re.S)
    return match.group(1) if match else html


MOBILE_NAV_MARKUP = (
    r'<nav class="mobnav".*?</nav>',
    r'<button type="button" class="navbtn".*?</button>',
)


def without_mobile_nav(html):
    """The mobile menu is a deliberate addition. Removing it lets the original
    fidelity guarantees stay exact instead of being loosened into vagueness."""
    for pattern in MOBILE_NAV_MARKUP:
        html = re.sub(pattern, "", html, flags=re.S)
    return html


def class_usage(html):
    """How many times each CSS class appears — what the stylesheet actually keys off."""
    counter = Counter()
    for attrs in re.findall(r"<\w+([^>]*)>", body(html)):
        found = re.search(r'class="([^"]*)"', attrs)
        if found:
            for name in found.group(1).split():
                counter[name] += 1
    return counter


class SeededPageTestCase(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_all", stdout=StringIO())


class PageRenderTests(SeededPageTestCase):
    def test_every_public_page_renders(self):
        for path in [
            "/az/", "/ru/", "/az/haqqimizda/", "/az/avadanliq/", "/az/layiheler/",
            "/az/komanda/", "/az/elaqe/",
        ]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_detail_pages_render(self):
        for path in ["/az/layiheler/yay-sehnesi-acilisi/", "/az/komanda/anar-selimov/"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_homepage_keeps_every_section_anchor(self):
        html = self.client.get("/az/").content.decode()
        for anchor in ["ana", "haqqimizda", "avadanliq", "layiheler", "komanda", "elaqe"]:
            self.assertIn(f'id="{anchor}"', html)

    def test_homepage_renders_seeded_content_counts(self):
        html = self.client.get("/az/").content.decode()
        self.assertEqual(html.count('class="member rv"'), 8)
        self.assertEqual(html.count('class="proj-card rv"'), 9)
        self.assertEqual(html.count('class="eq-card rv"'), 3)


class DesignFidelityTests(SeededPageTestCase):
    """Guards the promise that the refactor changed behaviour, not appearance."""

    def setUp(self):
        super().setUp()
        self.original = ORIGINAL_HTML.read_text()
        self.rendered = self.client.get("/az/").content.decode()

    def test_no_styled_class_changed_how_often_it_is_used(self):
        """Behaviour-only hook classes (no rule in site.css) are allowed to appear;
        anything the stylesheet actually targets must be used identically."""
        stylesheet = (Path(settings.BASE_DIR) / "static/css/site.css").read_text()
        original = class_usage(self.original)
        rendered = class_usage(without_mobile_nav(self.rendered))

        drifted = {}
        for name in set(original) | set(rendered):
            before, after = original.get(name, 0), rendered.get(name, 0)
            if before == after:
                continue
            if re.search(r"\.%s\b" % re.escape(name), stylesheet):
                drifted[name] = (before, after)

        self.assertEqual(drifted, {}, f"Styled class usage drifted: {drifted}")

    def test_added_classes_are_javascript_hooks_only(self):
        stylesheet = (Path(settings.BASE_DIR) / "static/css/site.css").read_text()
        added = set(class_usage(without_mobile_nav(self.rendered))) - set(
            class_usage(self.original)
        )
        styled = [n for n in added if re.search(r"\.%s\b" % re.escape(n), stylesheet)]
        self.assertEqual(styled, [], f"New classes carry styling: {styled}")

    def test_no_original_element_was_dropped(self):
        def skeleton(html):
            return Counter(
                (tag, (re.search(r'class="([^"]*)"', attrs) or [None, ""])[1])
                for tag, attrs in re.findall(r"<(\w+)([^>]*)>", body(html))
            )

        missing = skeleton(self.original) - skeleton(self.rendered)
        self.assertEqual(dict(missing), {})

    def test_only_expected_elements_were_added(self):
        # 8 team-name links + 1 language switcher + 1 CSRF input.
        extra_links = self.rendered.count("/az/komanda/") - self.original.count("komanda/")
        self.assertIn("csrfmiddlewaretoken", self.rendered)
        self.assertGreater(extra_links, 0)

    def _original_css(self):
        return re.search(r"<style>(.*?)</style>", self.original, re.S).group(1).strip()

    def test_stylesheet_is_external_and_keeps_the_original_css_verbatim(self):
        """Mobile work appends; it never edits. Because the original block is
        still an exact prefix, no desktop rule can have been changed."""
        self.assertNotIn("<style>", self.rendered)
        self.assertIn("css/site.css", self.rendered)
        stylesheet = (Path(settings.BASE_DIR) / "static/css/site.css").read_text().strip()
        self.assertTrue(
            stylesheet.startswith(self._original_css()),
            "site.css no longer starts with the original index.html CSS verbatim",
        )

    def test_appended_css_only_reaches_touch_and_small_screens(self):
        """Everything added after the original block must sit inside a mobile or
        touch media query, so the desktop rendering is protected structurally
        rather than by inspection."""
        stylesheet = (Path(settings.BASE_DIR) / "static/css/site.css").read_text().strip()
        tail = re.sub(r"/\*.*?\*/", "", stylesheet[len(self._original_css()):], flags=re.S)

        # Remove each @media block wholesale so only unscoped rules remain.
        out, i = [], 0
        while i < len(tail):
            if tail.startswith("@media", i):
                depth, j = 1, tail.index("{", i) + 1
                while j < len(tail) and depth:
                    depth += (tail[j] == "{") - (tail[j] == "}")
                    j += 1
                i = j
                continue
            out.append(tail[i])
            i += 1

        selectors = [
            " ".join(s.split()) for s in re.findall(r"([^{}]+)\{", "".join(out)) if s.strip()
        ]
        allowed = {
            ".navbtn",  # new element, display:none until a mobile query shows it
            "a,button,input,textarea,select,summary",  # -webkit-tap-highlight-color
            "a,button,.dock a,.navbtn",  # touch-action
        }
        self.assertEqual(
            [s for s in selectors if s not in allowed],
            [],
            "Appended CSS escapes its mobile scope",
        )

    def test_no_template_comment_leaks_into_the_html(self):
        # Django's {# #} is single-line only; a multi-line one renders as text.
        for marker in ["{#", "#}", "Photo stays unwrapped", "Absolute anchors", "JS posts to"]:
            self.assertNotIn(marker, self.rendered)


class ContactFormIntegrationTests(SeededPageTestCase):
    def setUp(self):
        super().setUp()
        self.html = self.client.get("/az/").content.decode()

    def test_form_points_at_the_api_endpoint(self):
        self.assertIn('data-endpoint="/api/v1/contact/messages/"', self.html)

    def test_field_names_match_the_serializer(self):
        for name in ["name", "email", "phone", "message"]:
            self.assertIn(f'name="{name}"', self.html)

    def test_form_has_a_no_js_fallback_action(self):
        self.assertIn('action="/az/elaqe/submit/"', self.html)
        self.assertIn("csrfmiddlewaretoken", self.html)

    def test_javascript_messages_are_localised_through_data_attributes(self):
        russian = self.client.get("/ru/").content.decode()
        self.assertIn("Отправляется...", russian)
        self.assertIn("Göndərilir...", self.html)


class LocalisationTests(SeededPageTestCase):
    def test_chrome_text_is_translated_and_does_not_leak(self):
        russian = self.client.get("/ru/").content.decode()
        self.assertIn("О нас", russian)
        self.assertNotIn("Haqqımızda", russian)

    def test_database_content_follows_the_active_language(self):
        self.assertIn("İLHAM VERƏN", self.client.get("/az/").content.decode())
        self.assertIn("ВДОХНОВЛЯЮЩИЕ", self.client.get("/ru/").content.decode())

    def test_language_switcher_links_to_the_other_locale(self):
        self.assertIn('href="/ru/"', self.client.get("/az/").content.decode())
        self.assertIn('href="/az/"', self.client.get("/ru/").content.decode())

    def test_switcher_preserves_the_current_page(self):
        html = self.client.get("/az/layiheler/").content.decode()
        self.assertIn('href="/ru/layiheler/"', html)


class HeaderNavigationTests(SeededPageTestCase):
    """The header links to standalone pages; the dock keeps in-page scrolling."""

    def test_navbar_points_at_standalone_pages(self):
        nav = re.search(
            r'<nav class="topnav">(.*?)</nav>', self.client.get("/az/").content.decode(), re.S
        ).group(1)
        for url in ["/az/haqqimizda/", "/az/avadanliq/", "/az/layiheler/", "/az/komanda/", "/az/elaqe/"]:
            self.assertIn(f'href="{url}"', nav)

    def test_navbar_has_no_homepage_anchors_left(self):
        nav = re.search(
            r'<nav class="topnav">(.*?)</nav>', self.client.get("/az/").content.decode(), re.S
        ).group(1)
        for anchor in ["#haqqimizda", "#avadanliq", "#layiheler", "#komanda", "#elaqe"]:
            self.assertNotIn(anchor, nav)

    def test_navbar_keeps_the_active_language_prefix(self):
        nav = re.search(
            r'<nav class="topnav">(.*?)</nav>', self.client.get("/ru/").content.decode(), re.S
        ).group(1)
        self.assertIn('href="/ru/komanda/"', nav)
        self.assertNotIn('href="/az/komanda/"', nav)

    def test_dock_still_scrolls_within_the_homepage(self):
        dock = re.search(
            r'<nav class="dock"(.*?)</nav>', self.client.get("/az/").content.decode(), re.S
        ).group(1)
        for anchor in ["#ana", "#haqqimizda", "#avadanliq", "#layiheler", "#komanda", "#elaqe"]:
            self.assertIn(anchor, dock)

    def test_each_standalone_page_has_its_own_title(self):
        expected = {
            "/az/haqqimizda/": "Haqqımızda",
            "/az/avadanliq/": "Avadanlıqlar",
            "/az/layiheler/": "Layihələr",
            "/az/komanda/": "Komanda",
            "/az/elaqe/": "Əlaqə",
            "/ru/haqqimizda/": "О нас",
            "/ru/komanda/": "Команда",
            "/ru/elaqe/": "Контакты",
        }
        for path, title in expected.items():
            with self.subTest(path=path):
                html = self.client.get(path).content.decode()
                self.assertIn(f"<title>{title} |", html)


class TranslationCatalogueTests(SeededPageTestCase):
    def test_no_string_is_left_untranslated(self):
        catalogue = Path(settings.BASE_DIR) / "locale/ru/LC_MESSAGES/django.po"
        text = catalogue.read_text()
        empty = []
        for match in re.finditer(r'^msgid ((?:"[^"]*"\n)+)msgstr ((?:"[^"]*"\n?)+)', text, re.M):
            msgid = "".join(re.findall(r'"([^"]*)"', match.group(1)))
            msgstr = "".join(re.findall(r'"([^"]*)"', match.group(2)))
            if msgid and not msgstr:
                empty.append(msgid)
        self.assertEqual(empty, [], f"Russian catalogue has untranslated entries: {empty}")


class SeoOnPageTests(SeededPageTestCase):
    def test_pages_expose_localised_titles_and_hreflang(self):
        for path, expected in [("/az/", "az"), ("/ru/", "ru")]:
            with self.subTest(path=path):
                html = self.client.get(path).content.decode()
                self.assertIn('hreflang="az"', html)
                self.assertIn('hreflang="ru"', html)
                self.assertIn("application/ld+json", html)
                self.assertIn(f'<html lang="{expected}"', html)

    def test_project_detail_uses_project_specific_seo(self):
        html = self.client.get("/az/layiheler/yay-sehnesi-acilisi/").content.decode()
        self.assertIn("<title>Yay Səhnəsi Açılışı", html)

    @override_settings()
    def test_pages_are_noindex_until_indexing_is_enabled(self):
        self.assertIn("noindex", self.client.get("/az/").content.decode())
