"""The admin has to actually expose the fields the site was extended with.

A model field, a migration and a registered inline can all be correct while the
edit page still shows nothing — so these assert against the rendered admin.
"""

import re
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command

from core.testing import BaseTestCase


class AdminSurfaceTests(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_all", stdout=StringIO())

    def setUp(self):
        super().setUp()
        user = get_user_model().objects.create_superuser(
            "surface", "s@example.com", "Xq7!vm2Zt9"
        )
        self.client.force_login(user)

    def _html(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200, path)
        return response.content.decode()

    def test_the_project_page_carries_the_gallery_inline(self):
        from projects.models import Project

        project = Project.objects.first()
        html = self._html(f"/admin/projects/project/{project.pk}/change/")

        self.assertIn("Qalereya", html)
        names = set(re.findall(r'name="(gallery-0-[a-z_]+)"', html))
        for field in ["kind", "image", "image_url", "video", "video_url", "order"]:
            with self.subTest(field=field):
                self.assertIn(f"gallery-0-{field}", names)

    def test_the_gallery_caption_is_editable_in_both_languages(self):
        from projects.models import Project

        html = self._html(
            f"/admin/projects/project/{Project.objects.first().pk}/change/"
        )
        self.assertIn('name="gallery-0-caption_az"', html)
        self.assertIn('name="gallery-0-caption_ru"', html)

    def test_an_empty_row_is_offered_for_a_new_item(self):
        """Without the __prefix__ template row, "add another" cannot work."""
        from projects.models import Project

        html = self._html(
            f"/admin/projects/project/{Project.objects.first().pk}/change/"
        )
        self.assertIn("gallery-__prefix__-kind", html)

    def test_the_team_page_carries_phone_and_email(self):
        from team.models import TeamMember

        html = self._html(
            f"/admin/team/teammember/{TeamMember.objects.first().pk}/change/"
        )
        self.assertRegex(html, r'<input[^>]*name="phone"')
        self.assertRegex(html, r'<input[^>]*name="email"')

    def test_the_team_list_shows_the_contact_columns(self):
        html = self._html("/admin/team/teammember/")
        self.assertIn("Telefon", html)
        self.assertIn("Email", html)

    def test_the_lead_list_offers_the_attachment(self):
        from contact.models import ContactMessage

        ContactMessage.objects.create(
            name="Müştəri", email="m@example.com",
            phone="+994501234567", message="brif",
        )
        html = self._html("/admin/contact/contactmessage/")
        self.assertIn("Fayl", html)
