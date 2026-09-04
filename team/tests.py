from django.test import TestCase

from core.testing import BaseTestCase

from team.models import TeamMember


class TeamMemberModelTests(BaseTestCase):
    def test_slug_is_auto_generated_from_azerbaijani_name(self):
        member = TeamMember.objects.create(name="Günel Xəlilova", role="Kommunikasiya Rəhbəri")
        self.assertEqual(member.slug, "gunel-xelilova")

    def test_duplicate_names_get_distinct_slugs(self):
        first = TeamMember.objects.create(name="Anar Səlimov", role="Direktor")
        second = TeamMember.objects.create(name="Anar Səlimov", role="Menecer")
        self.assertEqual(first.slug, "anar-selimov")
        self.assertEqual(second.slug, "anar-selimov-2")

    def test_get_absolute_url_uses_slug(self):
        member = TeamMember.objects.create(name="Anar Səlimov", role="Direktor")
        self.assertIn("anar-selimov", member.get_absolute_url())


class TeamAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        TeamMember.objects.create(
            name="Anar Səlimov",
            role_az="Baş Prodakşn Direktoru",
            role_ru="Главный директор продакшна",
            photo_url="https://example.com/a.jpg",
        )

    def test_list_endpoint_returns_members_in_both_languages(self):
        response = self.client.get("/api/v1/team/")
        self.assertEqual(response.status_code, 200)
        member = response.json()[0]
        self.assertEqual(member["role_az"], "Baş Prodakşn Direktoru")
        self.assertEqual(member["role_ru"], "Главный директор продакшна")

    def test_detail_endpoint_includes_bio(self):
        response = self.client.get("/api/v1/team/anar-selimov/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("bio_az", response.json())

    def test_external_photo_url_passes_through(self):
        response = self.client.get("/api/v1/team/")
        self.assertEqual(response.json()[0]["display_photo_url"], "https://example.com/a.jpg")
