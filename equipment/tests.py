from django.db.utils import IntegrityError
from django.test import TestCase

from core.testing import BaseTestCase

from equipment.models import EquipmentCategory, EquipmentTag


class EquipmentModelTests(BaseTestCase):
    def test_tag_number_must_be_unique(self):
        EquipmentCategory.objects.create(tag_number="01", tag_label="Işıq", title="Səhnə İşıqları")
        with self.assertRaises(IntegrityError):
            EquipmentCategory.objects.create(tag_number="01", tag_label="Səs", title="Soundriglar")


class EquipmentAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        category = EquipmentCategory.objects.create(
            tag_number="01",
            tag_label_az="Işıq",
            tag_label_ru="Свет",
            title_az="Səhnə İşıqları",
            title_ru="Сценическое освещение",
            order=1,
        )
        EquipmentTag.objects.create(category=category, label_az="Moving Head", order=1)

    def test_categories_endpoint_returns_nested_tags(self):
        response = self.client.get("/api/v1/equipment/categories/")
        self.assertEqual(response.status_code, 200)
        category = response.json()[0]
        self.assertEqual(category["title_az"], "Səhnə İşıqları")
        self.assertEqual(category["title_ru"], "Сценическое освещение")
        self.assertEqual(len(category["tags"]), 1)
        self.assertEqual(category["tags"][0]["label_az"], "Moving Head")
