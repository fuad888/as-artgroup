from django.db import models

from core.models import SingletonModel


class HeroContent(SingletonModel):
    eyebrow = models.CharField(max_length=120, blank=True)
    heading_line1 = models.CharField(max_length=120, blank=True)
    heading_line2 = models.CharField(max_length=120, blank=True)
    heading_line3 = models.CharField(max_length=120, blank=True)
    lead = models.TextField(blank=True)
    cta_primary_label = models.CharField(max_length=60, blank=True)
    cta_secondary_label = models.CharField(max_length=60, blank=True)
    image = models.ImageField(upload_to="home/", blank=True)
    image_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "Hero məzmunu"
        verbose_name_plural = "Hero məzmunu"

    def __str__(self):
        return "Hero məzmunu"

    @property
    def display_image_url(self):
        return self.image.url if self.image else self.image_url


class HeroFeature(models.Model):
    ICON_CHOICES = [
        ("light", "İşıq"),
        ("sound", "Səs"),
        ("spark", "Prodakşn"),
    ]

    hero = models.ForeignKey(HeroContent, related_name="features", on_delete=models.CASCADE)
    icon_key = models.CharField(max_length=20, choices=ICON_CHOICES, default="light")
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Hero xüsusiyyəti"
        verbose_name_plural = "Hero xüsusiyyətləri"

    def __str__(self):
        return self.title
