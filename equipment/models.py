from django.db import models


class EquipmentCategory(models.Model):
    GRADIENT_CHOICES = [
        ("cool", "Cool"),
        ("warm", "Warm"),
        ("hot", "Hot"),
    ]

    tag_number = models.CharField(max_length=10, unique=True, help_text='Məs. "01"')
    tag_label = models.CharField(max_length=60)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="equipment/", blank=True)
    image_url = models.URLField(blank=True)
    gradient_key = models.CharField(max_length=10, choices=GRADIENT_CHOICES, default="cool")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Avadanlıq kateqoriyası"
        verbose_name_plural = "Avadanlıq kateqoriyaları"

    def __str__(self):
        return self.title

    @property
    def display_image_url(self):
        return self.image.url if self.image else self.image_url


class EquipmentTag(models.Model):
    category = models.ForeignKey(EquipmentCategory, related_name="tags", on_delete=models.CASCADE)
    label = models.CharField(max_length=60)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Avadanlıq etiketi"
        verbose_name_plural = "Avadanlıq etiketləri"

    def __str__(self):
        return self.label
