from django.db import models
from django.urls import reverse
from django.utils.text import Truncator

from core.utils import unique_slug


class ProjectCategory(models.Model):
    """Separate table (not CharField choices) so the badge text is translatable per row."""

    name = models.CharField(max_length=60)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Layihə kateqoriyası"
        verbose_name_plural = "Layihə kateqoriyaları"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)


class Project(models.Model):
    GRADIENT_CHOICES = [
        ("cool", "Cool"),
        ("warm", "Warm"),
        ("hot", "Hot"),
    ]

    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    category = models.ForeignKey(ProjectCategory, related_name="projects", on_delete=models.PROTECT)
    image = models.ImageField(upload_to="projects/", blank=True)
    image_url = models.URLField(blank=True)
    meta_primary = models.CharField(max_length=120, blank=True, help_text="Məs. məkan və ya detal")
    meta_secondary = models.CharField(max_length=120, blank=True, help_text="Məs. qonaq sayı, müddət")
    description = models.TextField(blank=True, help_text="Detal səhifəsi üçün")
    is_featured = models.BooleanField(default=False, help_text="Ana səhifədə göstərilsin")
    gradient_key = models.CharField(max_length=10, choices=GRADIENT_CHOICES, default="cool")
    order = models.PositiveIntegerField(default=0)
    meta_title = models.CharField(
        max_length=70, blank=True, help_text="Boş buraxılsa layihə başlığı istifadə olunur"
    )
    meta_description = models.CharField(
        max_length=160, blank=True, help_text="Boş buraxılsa təsvirdən götürülür"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Layihə"
        verbose_name_plural = "Layihələr"
        indexes = [
            # Homepage: filter is_featured, then order by `order`.
            models.Index(fields=["is_featured", "order"], name="project_featured_order_idx"),
            models.Index(fields=["order", "id"], name="project_order_idx"),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("projects:detail", kwargs={"slug": self.slug})

    @property
    def display_image_url(self):
        return self.image.url if self.image else self.image_url

    @property
    def seo_title(self):
        return self.meta_title or self.title

    @property
    def seo_description(self):
        return self.meta_description or Truncator(self.description).chars(160)


class ProjectMedia(models.Model):
    """Extra photos and video for a project, shown only on its detail page.

    Kept in its own table rather than more columns on Project because the count
    is open-ended and the order matters. Images and video share one model so a
    single ordered gallery can mix them.
    """

    IMAGE = "image"
    VIDEO = "video"
    KIND_CHOICES = [(IMAGE, "Şəkil"), (VIDEO, "Video")]

    project = models.ForeignKey(Project, related_name="gallery", on_delete=models.CASCADE)
    kind = models.CharField(max_length=8, choices=KIND_CHOICES, default=IMAGE, verbose_name="Növ")
    image = models.ImageField(
        upload_to="projects/gallery/",
        blank=True,
        verbose_name="Şəkil",
        help_text="Video üçün bu, önizləmə (poster) şəkli olur.",
    )
    image_url = models.URLField(blank=True, verbose_name="Şəkil linki")
    video = models.FileField(
        upload_to="projects/video/", blank=True, verbose_name="Video faylı", help_text="MP4"
    )
    video_url = models.URLField(
        blank=True,
        verbose_name="Video linki",
        help_text="YouTube, Vimeo və ya birbaşa .mp4 linki",
    )
    caption = models.CharField(max_length=200, blank=True, verbose_name="Başlıq")
    order = models.PositiveIntegerField(default=0, verbose_name="Sıra")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Qalereya elementi"
        verbose_name_plural = "Qalereya (şəkil və video)"
        indexes = [models.Index(fields=["project", "order"], name="projectmedia_order_idx")]

    def __str__(self):
        return f"{self.project.title} — {self.get_kind_display()} {self.order}"

    @property
    def is_video(self):
        return self.kind == self.VIDEO

    @property
    def display_image_url(self):
        """The thumbnail: the uploaded image, the linked one, or — for a video
        with neither — the project's own cover so the tile is never empty."""
        return self.image.url if self.image else (self.image_url or self.project.display_image_url)

    @property
    def display_video_url(self):
        return self.video.url if self.video else self.video_url

    @property
    def embed_url(self):
        """YouTube and Vimeo watch links have to become embed links, otherwise
        the iframe shows the site's own "refused to connect" page."""
        url = self.video_url or ""
        if not url:
            return ""
        if "youtube.com/watch" in url and "v=" in url:
            return "https://www.youtube.com/embed/" + url.split("v=")[1].split("&")[0]
        if "youtu.be/" in url:
            return "https://www.youtube.com/embed/" + url.split("youtu.be/")[1].split("?")[0]
        if "vimeo.com/" in url and "player.vimeo.com" not in url:
            return "https://player.vimeo.com/video/" + url.rstrip("/").split("/")[-1].split("?")[0]
        return ""

    @property
    def is_embed(self):
        return bool(self.embed_url)

    @property
    def is_file_video(self):
        """A direct file plays in <video>; an embed needs an iframe."""
        return self.is_video and bool(self.display_video_url) and not self.is_embed
