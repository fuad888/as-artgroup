from django.test import TestCase

from core.testing import BaseTestCase

from about.models import AboutContent, Stat


class AboutAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        about = AboutContent.load()
        about.heading_az = "Şəhərin enerjisini"
        about.heading_ru = "Энергию города"
        about.save()
        Stat.objects.create(
            about=about, number=22, label_az="Tədbirlər", label_ru="Мероприятия", order=1
        )

    def test_endpoint_returns_content_with_nested_stats(self):
        response = self.client.get("/api/v1/about/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["heading_az"], "Şəhərin enerjisini")
        self.assertEqual(data["heading_ru"], "Энергию города")
        self.assertEqual(len(data["stats"]), 1)
        self.assertEqual(data["stats"][0]["number"], 22)

    def test_singleton_is_created_on_demand(self):
        AboutContent.objects.all().delete()
        response = self.client.get("/api/v1/about/")
        self.assertEqual(response.status_code, 200)
