from django.db import models

from core.models import SingletonModel


class AboutContent(SingletonModel):
    eyebrow = models.CharField(max_length=120, blank=True)
    heading = models.CharField(max_length=255, blank=True)
    heading_accent = models.CharField(max_length=255, blank=True)
    lead = models.TextField(blank=True)
    body_paragraph_1 = models.TextField(blank=True)
    body_paragraph_2 = models.TextField(blank=True)
    image = models.ImageField(upload_to="about/", blank=True)
    image_url = models.URLField(blank=True)
    badge_title = models.CharField(max_length=120, blank=True)
    badge_subtitle = models.CharField(max_length=120, blank=True)
    cta_primary_label = models.CharField(max_length=60, blank=True)
    cta_secondary_label = models.CharField(max_length=60, blank=True)

    class Meta:
        verbose_name = "Haqqımızda məzmunu"
        verbose_name_plural = "Haqqımızda məzmunu"

    def __str__(self):
        return "Haqqımızda məzmunu"

    @property
    def display_image_url(self):
        return self.image.url if self.image else self.image_url


class Stat(models.Model):
    GRADIENT_CHOICES = [
        ("cool", "Cool"),
        ("warm", "Warm"),
        ("hot", "Hot"),
    ]

    about = models.ForeignKey(AboutContent, related_name="stats", on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    suffix = models.CharField(max_length=10, blank=True)
    label = models.CharField(max_length=80)
    description = models.CharField(max_length=255, blank=True)
    gradient_key = models.CharField(max_length=10, choices=GRADIENT_CHOICES, default="cool")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Statistika"
        verbose_name_plural = "Statistikalar"

    def __str__(self):
        return f"{self.number}{self.suffix} — {self.label}"
