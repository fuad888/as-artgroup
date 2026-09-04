from django.test import TestCase

from core.testing import BaseTestCase

from projects.models import Project, ProjectCategory


class ProjectModelTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.category = ProjectCategory.objects.create(name="Konsert", name_ru="Концерт")

    def test_slug_is_auto_generated_from_azerbaijani_title(self):
        project = Project.objects.create(title="Yay Səhnəsi Açılışı", category=self.category)
        self.assertEqual(project.slug, "yay-sehnesi-acilisi")

    def test_explicit_slug_is_kept(self):
        project = Project.objects.create(
            title="Yay Səhnəsi", slug="custom-slug", category=self.category
        )
        self.assertEqual(project.slug, "custom-slug")

    def test_category_slug_is_auto_generated(self):
        category = ProjectCategory.objects.create(name="Təntənəli Mərasim")
        self.assertEqual(category.slug, "tenteneli-merasim")

    def test_get_absolute_url_uses_slug(self):
        project = Project.objects.create(title="Arena Live", category=self.category)
        self.assertIn(project.slug, project.get_absolute_url())

    def test_display_image_url_falls_back_to_external_url(self):
        project = Project.objects.create(
            title="Arena Live", category=self.category, image_url="https://example.com/a.jpg"
        )
        self.assertEqual(project.display_image_url, "https://example.com/a.jpg")


class ProjectAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.concert = ProjectCategory.objects.create(name="Konsert", slug="konsert")
        self.expo = ProjectCategory.objects.create(name="Sərgi", slug="sergi")
        Project.objects.create(title="Arena Live", category=self.concert, is_featured=True)
        Project.objects.create(title="Design Expo", category=self.expo, is_featured=False)

    def test_list_returns_all_projects(self):
        response = self.client.get("/api/v1/projects/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 2)

    def test_filter_by_category_slug(self):
        response = self.client.get("/api/v1/projects/?category=konsert")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

    def test_filter_by_is_featured(self):
        response = self.client.get("/api/v1/projects/?is_featured=true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

    def test_detail_includes_description_in_both_languages(self):
        response = self.client.get("/api/v1/projects/arena-live/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("description_az", response.json())
        self.assertIn("description_ru", response.json())

    def test_unknown_slug_returns_404(self):
        response = self.client.get("/api/v1/projects/does-not-exist/")
        self.assertEqual(response.status_code, 404)
