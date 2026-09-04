from django.test import TestCase

from core.testing import BaseTestCase

from home.models import HeroContent, HeroFeature


class HeroAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        hero = HeroContent.load()
        hero.heading_line1_az = "İLHAM VERƏN"
        hero.heading_line1_ru = "ВДОХНОВЛЯЮЩИЕ"
        hero.save()
        HeroFeature.objects.create(
            hero=hero, icon_key="light", title_az="Peşəkar səhnə işığı", order=1
        )

    def test_hero_endpoint_returns_content_with_features(self):
        response = self.client.get("/api/v1/home/hero/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["heading_line1_az"], "İLHAM VERƏN")
        self.assertEqual(data["heading_line1_ru"], "ВДОХНОВЛЯЮЩИЕ")
        self.assertEqual(len(data["features"]), 1)
        self.assertEqual(data["features"][0]["icon_key"], "light")
