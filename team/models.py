from django.db import models
from django.urls import reverse
from django.utils.text import Truncator

from core.utils import unique_slug


class TeamMember(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    role = models.CharField(max_length=120)
    photo = models.ImageField(upload_to="team/", blank=True)
    photo_url = models.URLField(blank=True)
    bio = models.TextField(blank=True, help_text="Detal səhifəsi üçün")
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    meta_title = models.CharField(
        max_length=70, blank=True, help_text="Boş buraxılsa ad və vəzifə istifadə olunur"
    )
    meta_description = models.CharField(
        max_length=160, blank=True, help_text="Boş buraxılsa bio-dan götürülür"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Komanda üzvü"
        verbose_name_plural = "Komanda üzvləri"
        indexes = [models.Index(fields=["order", "id"], name="team_order_idx")]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("team:detail", kwargs={"slug": self.slug})

    @property
    def display_photo_url(self):
        return self.photo.url if self.photo else self.photo_url

    @property
    def seo_title(self):
        return self.meta_title or f"{self.name} — {self.role}"

    @property
    def seo_description(self):
        return self.meta_description or Truncator(self.bio).chars(160)
