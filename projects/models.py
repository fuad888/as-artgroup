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
