"""Phone and email on a team member: useful when present, absent by default."""

from core.testing import BaseTestCase
from team.models import TeamMember


class TeamContactTests(BaseTestCase):
    def _member(self, **extra):
        return TeamMember.objects.create(name="Anar Səlimov", role="Prodakşn", **extra)

    def test_both_fields_are_optional(self):
        member = self._member()
        member.full_clean()  # would raise if either were required
        self.assertEqual(member.phone, "")
        self.assertEqual(member.email, "")

    def test_a_tap_on_the_number_places_a_call(self):
        member = self._member(phone="+994 51 555 77 44")
        self.assertEqual(member.phone_href, "tel:+994515557744")

    def test_a_tap_on_the_address_opens_the_mail_app(self):
        member = self._member(email="anar@as-artgroup.az")
        self.assertEqual(member.email_href, "mailto:anar@as-artgroup.az")

    def test_empty_fields_produce_no_href(self):
        member = self._member()
        self.assertEqual(member.phone_href, "")
        self.assertEqual(member.email_href, "")

    def test_the_detail_page_shows_them_when_set(self):
        member = self._member(phone="+994 51 555 77 44", email="anar@as-artgroup.az")
        html = self.client.get(member.get_absolute_url()).content.decode()
        self.assertIn("tel:+994515557744", html)
        self.assertIn("mailto:anar@as-artgroup.az", html)

    def test_the_detail_page_shows_nothing_when_unset(self):
        member = self._member()
        html = self.client.get(member.get_absolute_url()).content.decode()
        self.assertNotIn("member__contact", html)

    def test_only_the_field_that_is_filled_appears(self):
        member = self._member(email="anar@as-artgroup.az")
        html = self.client.get(member.get_absolute_url()).content.decode()
        self.assertIn("mailto:anar@as-artgroup.az", html)
        self.assertNotIn('href="tel:', html)
