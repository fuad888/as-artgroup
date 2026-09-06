from django.db import models

from .validators import validate_attachment, validate_phone


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=32, validators=[validate_phone])
    message = models.TextField()
    # Optional: a customer may attach a brief or presentation.
    attachment = models.FileField(
        upload_to="contact/%Y/%m/",
        blank=True,
        validators=[validate_attachment],
        verbose_name="Əlavə fayl",
        help_text="PDF, Word və ya Excel — maksimum 10 MB",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_handled = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Əlaqə mesajı"
        verbose_name_plural = "Əlaqə mesajları"
        indexes = [
            # Leads are the one table that grows without bound: admin lists them
            # newest-first and filters on the triage flag.
            models.Index(fields=["-created_at"], name="contact_created_idx"),
            models.Index(fields=["is_handled", "-created_at"], name="contact_handled_idx"),
        ]

    def __str__(self):
        return f"{self.name} <{self.email}>"
