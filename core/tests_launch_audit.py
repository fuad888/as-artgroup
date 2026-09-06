import re
from pathlib import Path
from django.conf import settings
"""Route, error-page and cache-policy coverage for the deployed site."""

from django.core.management import call_command
from django.http import HttpResponse
from django.test import override_settings
from django.urls import path
from io import StringIO

from contact.models import ContactMessage
from core.testing import BaseTestCase


def boom(request):
    raise RuntimeError("deliberate failure")


urlpatterns = [path("boom/", boom)]


@override_settings(ROOT_URLCONF=__name__, DEBUG=False)
class ServerErrorPageTests(BaseTestCase):
    """A 500 must stay on-brand and must never leak internals."""

    def test_the_error_page_is_rendered_not_a_traceback(self):
        self.client.raise_request_exception = False
        response = self.client.get("/boom/")
        self.assertEqual(response.status_code, 500)
        body = response.content.decode()
        self.assertNotIn("RuntimeError", body)
        self.assertNotIn("Traceback", body)
        self.assertNotIn("deliberate failure", body)

    def test_the_error_page_carries_the_site_design(self):
        self.client.raise_request_exception = False
        body = self.client.get("/boom/").content.decode()
        self.assertIn("AS-ART", body)
        # A way back, so a broken page is not a dead end.
        self.assertIn("href=", body)


class RouteStatusTests(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_all", stdout=StringIO())

    PAGES = [
        "/az/", "/ru/", "/az/haqqimizda/", "/ru/haqqimizda/", "/az/avadanliq/",
        "/ru/avadanliq/", "/az/layiheler/", "/ru/layiheler/", "/az/komanda/",
        "/ru/komanda/", "/az/elaqe/", "/ru/elaqe/",
    ]
    MISSING = [
        "/az/yoxdur/", "/ru/yoxdur/", "/az/layiheler/olmayan/",
        "/az/komanda/olmayan/", "/tamamile-yanlis/",
    ]

    def test_every_page_answers_200_in_both_languages(self):
        for path_ in self.PAGES:
            with self.subTest(path=path_):
                self.assertEqual(self.client.get(path_).status_code, 200)

    def test_unknown_addresses_answer_404(self):
        for path_ in self.MISSING:
            with self.subTest(path=path_):
                self.assertEqual(self.client.get(path_).status_code, 404)

    def test_the_404_page_offers_a_way_back(self):
        body = self.client.get("/az/yoxdur/").content.decode()
        self.assertIn("AS-ART", body)
        self.assertIn("href=", body)

    def test_api_reports_missing_objects_as_404(self):
        for path_ in ["/api/v1/projects/olmayan/", "/api/v1/team/olmayan/"]:
            with self.subTest(path=path_):
                self.assertEqual(self.client.get(path_).status_code, 404)


class CachePolicyTests(BaseTestCase):
    def test_crawler_files_are_cacheable(self):
        """Crawlers refetch these constantly; they change only with content."""
        for path_ in ["/robots.txt", "/sitemap.xml"]:
            with self.subTest(path=path_):
                header = self.client.get(path_).get("Cache-Control", "")
                self.assertIn("public", header)
                self.assertIn("s-maxage", header)

    def test_pages_revalidate_so_a_deploy_is_seen_at_once(self):
        header = self.client.get("/az/").get("Cache-Control", "")
        self.assertIn("no-cache", header)
        self.assertIn("private", header)

    def test_api_responses_stay_publicly_cacheable(self):
        header = self.client.get("/api/v1/projects/").get("Cache-Control", "")
        self.assertIn("public", header)
        self.assertIn("s-maxage", header)


class ContactThrottleSharingTests(BaseTestCase):
    """The JS path and the no-JS form must not each get their own allowance."""

    FORM = {"name": "T", "email": "t@example.com",
            "phone": "+994501234567", "message": "salam"}

    def test_the_plain_form_is_rate_limited_too(self):
        for _ in range(8):
            self.client.post("/az/elaqe/submit/", self.FORM)
        self.assertLessEqual(ContactMessage.objects.count(), 5)

    def test_the_two_paths_share_one_allowance(self):
        for _ in range(5):
            self.client.post("/az/elaqe/submit/", self.FORM)
        response = self.client.post(
            "/api/v1/contact/messages/", self.FORM, content_type="application/json"
        )
        self.assertEqual(response.status_code, 429)

    def test_a_blocked_submission_still_returns_the_visitor_to_the_page(self):
        for _ in range(6):
            response = self.client.post("/az/elaqe/submit/", self.FORM)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/elaqe/", response["Location"])


class HiddenOverlayTests(BaseTestCase):
    """A full-screen overlay that ignores `hidden` swallows every click on the
    page beneath it, and looks like nothing at all — the lightbox did exactly
    this. Author CSS outranks the browser's [hidden]{display:none}, so any
    element rendered with `hidden` whose class sets `display` needs its own
    [hidden] rule."""

    HIDDEN_TAG = re.compile(r"<\w+[^>]*?\shidden(?=[\s>])[^>]*>", re.S)

    def _templates(self):
        root = Path(settings.BASE_DIR)
        for path in root.rglob("*.html"):
            if any(part in {"venv", "staticfiles", "node_modules"} for part in path.parts):
                continue
            yield path

    def test_no_hidden_element_is_forced_visible_by_a_display_rule(self):
        css = (Path(settings.BASE_DIR) / "static/css/site.css").read_text()
        offenders = []

        for path in self._templates():
            for tag in self.HIDDEN_TAG.findall(path.read_text()):
                classes = re.search(r'class="([^"]*)"', tag)
                if not classes:
                    continue
                for name in classes.group(1).split():
                    sets_display = re.search(
                        r"\.%s\s*\{[^}]*display\s*:" % re.escape(name), css
                    )
                    has_guard = re.search(r"\.%s\[hidden\]" % re.escape(name), css)
                    if sets_display and not has_guard:
                        offenders.append(f"{path.name}: .{name}")

        self.assertEqual(
            offenders, [], "hidden element kept visible by a display rule: %s" % offenders
        )

    def test_the_lightbox_specifically_respects_hidden(self):
        css = (Path(settings.BASE_DIR) / "static/css/site.css").read_text()
        self.assertRegex(css, r"\.lightbox\[hidden\]\s*\{[^}]*display\s*:\s*none")
