"""The homepage equipment tiles have to lead somewhere."""

from core.testing import BaseTestCase
from equipment.models import EquipmentCategory


class EquipmentTileLinkTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        EquipmentCategory.objects.create(title="İşıq", tag_number="01", tag_label="Light")

    def test_each_tile_links_to_the_equipment_page(self):
        """They had a hover effect but no href at all."""
        html = self.client.get("/az/").content.decode()
        self.assertIn('class="eq-card__link"', html)
        self.assertIn('href="/az/avadanliq/"', html)

    def test_the_link_is_reachable(self):
        self.assertEqual(self.client.get("/az/avadanliq/").status_code, 200)

    def test_the_link_is_labelled_for_screen_readers(self):
        html = self.client.get("/az/").content.decode()
        self.assertIn("aria-label=\"İşıq", html)

    def test_the_russian_page_links_to_the_russian_url(self):
        html = self.client.get("/ru/").content.decode()
        self.assertIn('href="/ru/avadanliq/"', html)
