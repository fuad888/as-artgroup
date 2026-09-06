"""The site's default language is Azerbaijani, not the visitor's browser setting."""

from django.test import Client

from core.testing import BaseTestCase


class DefaultLanguageTests(BaseTestCase):
    def _root(self, accept_language=None):
        headers = {"accept-language": accept_language} if accept_language else {}
        return Client(headers=headers).get("/")

    def test_a_russian_browser_still_lands_on_azerbaijani(self):
        """This is the bug: a phone set to Russian opened /ru/."""
        self.assertEqual(self._root("ru-RU,ru;q=0.9").headers["Location"], "/az/")

    def test_other_languages_land_on_azerbaijani_too(self):
        for header in ["en-US,en;q=0.9", "tr-TR,tr;q=0.9", "de-DE", "ru"]:
            with self.subTest(accept_language=header):
                self.assertEqual(self._root(header).headers["Location"], "/az/")

    def test_no_header_lands_on_azerbaijani(self):
        self.assertEqual(self._root().headers["Location"], "/az/")

    def test_the_switcher_still_works_and_sticks(self):
        """Only the browser's guess is ignored; an explicit choice is kept."""
        client = Client(headers={"accept-language": "en-US"})
        client.post("/i18n/setlang/", {"language": "ru", "next": "/"}, follow=True)
        self.assertEqual(client.get("/").headers["Location"], "/ru/")

    def test_an_explicit_russian_url_is_never_redirected_away(self):
        self.assertEqual(self.client.get("/ru/").status_code, 200)
