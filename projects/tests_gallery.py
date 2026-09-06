"""Extra photos and video per project, shown only on the detail page."""

from core.testing import BaseTestCase
from projects.models import Project, ProjectCategory, ProjectMedia


class GalleryModelTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.category = ProjectCategory.objects.create(name="Konsert", slug="konsert")
        self.project = Project.objects.create(
            title="Yay Səhnəsi", category=self.category,
            image_url="https://example.com/cover.jpg",
        )

    def test_a_video_without_its_own_thumbnail_borrows_the_project_cover(self):
        """A gallery tile is never blank."""
        item = ProjectMedia.objects.create(
            project=self.project, kind=ProjectMedia.VIDEO,
            video_url="https://www.youtube.com/watch?v=abc123",
        )
        self.assertEqual(item.display_image_url, "https://example.com/cover.jpg")

    def test_a_youtube_watch_link_becomes_an_embed_link(self):
        """A watch URL in an iframe renders YouTube's refusal page instead."""
        item = ProjectMedia(kind=ProjectMedia.VIDEO,
                            video_url="https://www.youtube.com/watch?v=abc123&t=30")
        self.assertEqual(item.embed_url, "https://www.youtube.com/embed/abc123")

    def test_a_short_youtube_link_becomes_an_embed_link(self):
        item = ProjectMedia(kind=ProjectMedia.VIDEO, video_url="https://youtu.be/abc123?t=5")
        self.assertEqual(item.embed_url, "https://www.youtube.com/embed/abc123")

    def test_a_vimeo_link_becomes_an_embed_link(self):
        item = ProjectMedia(kind=ProjectMedia.VIDEO, video_url="https://vimeo.com/987654")
        self.assertEqual(item.embed_url, "https://player.vimeo.com/video/987654")

    def test_a_direct_mp4_is_played_as_a_file_not_embedded(self):
        item = ProjectMedia(kind=ProjectMedia.VIDEO, video_url="https://cdn.example.com/a.mp4")
        self.assertEqual(item.embed_url, "")
        self.assertTrue(item.is_file_video)

    def test_items_keep_their_configured_order(self):
        for i in (3, 1, 2):
            ProjectMedia.objects.create(project=self.project, order=i, caption=f"c{i}")
        self.assertEqual([m.order for m in self.project.gallery.all()], [1, 2, 3])

    def test_deleting_a_project_takes_its_gallery_with_it(self):
        ProjectMedia.objects.create(project=self.project)
        self.project.delete()
        self.assertEqual(ProjectMedia.objects.count(), 0)


class GalleryPageTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        category = ProjectCategory.objects.create(name="Konsert", slug="konsert")
        self.project = Project.objects.create(
            title="Yay Səhnəsi", category=category, image_url="https://example.com/c.jpg"
        )

    def _html(self):
        return self.client.get(self.project.get_absolute_url()).content.decode()

    def test_no_gallery_markup_when_there_is_nothing_to_show(self):
        html = self._html()
        self.assertNotIn('class="gallery', html)
        self.assertNotIn('id="lightbox"', html)

    def test_the_gallery_and_lightbox_appear_once_there_are_items(self):
        ProjectMedia.objects.create(project=self.project, image_url="https://example.com/1.jpg")
        html = self._html()
        self.assertIn('id="gallery"', html)
        self.assertIn('id="lightbox"', html)

    def test_each_item_carries_what_the_lightbox_needs(self):
        ProjectMedia.objects.create(
            project=self.project, image_url="https://example.com/1.jpg", caption="Səhnə"
        )
        html = self._html()
        self.assertIn('data-full="https://example.com/1.jpg"', html)
        self.assertIn('data-caption="Səhnə"', html)

    def test_a_video_item_is_marked_as_one(self):
        ProjectMedia.objects.create(
            project=self.project, kind=ProjectMedia.VIDEO,
            video_url="https://www.youtube.com/watch?v=abc123",
        )
        html = self._html()
        self.assertIn('data-kind="video"', html)
        self.assertIn('data-embed="https://www.youtube.com/embed/abc123"', html)
        self.assertIn("gallery__play", html)

    def test_the_gallery_is_only_on_the_detail_page(self):
        ProjectMedia.objects.create(project=self.project, image_url="https://example.com/1.jpg")
        for path in ["/az/", "/az/layiheler/"]:
            with self.subTest(path=path):
                self.assertNotIn('id="gallery"', self.client.get(path).content.decode())

    def test_the_gallery_costs_no_query_per_item(self):
        """prefetch_related, so a 40-photo gallery is one extra query, not 40."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        def count():
            from django.core.cache import cache
            cache.clear()
            with CaptureQueriesContext(connection) as ctx:
                self.client.get(self.project.get_absolute_url())
            return len(ctx)

        empty = count()
        for i in range(20):
            ProjectMedia.objects.create(project=self.project, image_url=f"https://e.com/{i}.jpg")
        full = count()
        # One extra query for the prefetch itself, and nothing per item.
        self.assertLessEqual(full, empty + 1, f"{empty} -> {full} sorğu")
