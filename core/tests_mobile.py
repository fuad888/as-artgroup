"""Guards for the mobile pass: the header must stay usable on a phone, and the
per-frame work that froze it must not come back."""

import re
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from io import StringIO

from core.testing import BaseTestCase

CSS = Path(settings.BASE_DIR) / "static/css/site.css"
JS = Path(settings.BASE_DIR) / "static/js/site.js"

NAV_PAGES = ["/az/", "/az/haqqimizda/", "/az/avadanliq/", "/az/layiheler/",
             "/az/komanda/", "/az/elaqe/"]


class MobileNavigationTests(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_all", stdout=StringIO())

    def setUp(self):
        super().setUp()
        self.html = self.client.get("/az/").content.decode()

    def _panel(self, html=None):
        match = re.search(r'<nav class="mobnav".*?</nav>', html or self.html, re.S)
        self.assertIsNotNone(match, "mobile menu panel missing")
        return match.group(0)

    def test_every_page_carries_the_mobile_menu(self):
        """Below 1080px .topnav is display:none, so a page without this panel
        has no header navigation at all."""
        for path in NAV_PAGES:
            with self.subTest(path=path):
                self.assertIn('id="mobnav"', self.client.get(path).content.decode())

    def test_menu_holds_every_destination_the_desktop_nav_has(self):
        panel = self._panel()
        for url in ["/az/haqqimizda/", "/az/avadanliq/", "/az/layiheler/",
                    "/az/komanda/", "/az/elaqe/"]:
            with self.subTest(url=url):
                self.assertIn(f'href="{url}"', panel)

    def test_menu_carries_the_language_switcher(self):
        """It lives inside .topnav, so on a phone it was unreachable entirely."""
        self.assertIn('hreflang="ru"', self._panel())

    def test_menu_and_desktop_nav_cannot_drift_apart(self):
        topnav = re.search(r'<nav class="topnav">(.*?)</nav>', self.html, re.S).group(1)
        hrefs = lambda block: sorted(re.findall(r'href="([^"]+)"', block))
        panel_links = [h for h in hrefs(self._panel()) if not h.startswith("#")]
        # The panel additionally carries the CTA that the header hides under 640px.
        self.assertEqual(hrefs(topnav), sorted(set(panel_links) & set(hrefs(topnav))))
        self.assertTrue(set(hrefs(topnav)).issubset(set(panel_links)))

    def test_toggle_is_wired_to_the_panel_and_starts_closed(self):
        button = re.search(r"<button[^>]*class=\"navbtn\"[^>]*>", self.html, re.S).group(0)
        self.assertIn('aria-controls="mobnav"', button)
        self.assertIn('aria-expanded="false"', button)
        self.assertRegex(self._panel(), r"<nav class=\"mobnav\"[^>]*\shidden")

    def test_toggle_is_a_button_not_a_link(self):
        """A bare <a href="#"> would jump the page before the handler runs."""
        self.assertIn('<button type="button" class="navbtn"', self.html)


class MobilePerformanceRegressionTests(BaseTestCase):
    """Each assertion here maps to a specific cause of the freeze on phones."""

    def setUp(self):
        super().setUp()
        self.css = CSS.read_text()
        self.js = JS.read_text()

    def _mobile_block(self):
        marker = "MOBILE OPTIMISATION"
        self.assertIn(marker, self.css)
        return self.css[self.css.index(marker):]

    def test_full_screen_blurred_blobs_stop_animating_on_phones(self):
        """Four blurred, screen-blended layers animating forever forced the
        compositor to re-blur a full-screen surface every frame."""
        self.assertRegex(self._mobile_block(), r"\.blob\{[^}]*animation:none")

    def test_blobs_stop_blending_on_phones(self):
        self.assertRegex(self._mobile_block(), r"\.blob\{[^}]*mix-blend-mode:normal")

    def test_the_fixed_dock_drops_its_backdrop_filter_on_phones(self):
        """A fixed blurred bar re-samples everything scrolling behind it."""
        self.assertRegex(self._mobile_block(), r"\.dock\{[^}]*backdrop-filter:none")

    def test_scroll_handler_does_not_read_layout(self):
        """offsetTop inside the scroll path forces a synchronous layout flush;
        offsets are measured up front and cached instead."""
        scroll_path = self.js[self.js.index("var apply = function()"):]
        scroll_path = scroll_path[: scroll_path.index("var queued")]
        for prop in ["offsetTop", "getBoundingClientRect", "offsetHeight", "clientHeight"]:
            with self.subTest(prop=prop):
                self.assertNotIn(prop, scroll_path)

    def test_scroll_listener_is_throttled_and_passive(self):
        self.assertIn("requestAnimationFrame", self.js)
        self.assertIn("window.addEventListener('scroll', onScroll, {passive:true})", self.js)

    def test_hover_effects_are_disabled_where_there_is_no_pointer(self):
        """On touch, :hover latches after a tap and stays stuck."""
        self.assertIn("@media (hover:none)", self.css)

    def test_no_debug_logging_of_submitted_form_data(self):
        self.assertNotIn("console.log", self.js)
