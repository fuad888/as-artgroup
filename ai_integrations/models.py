from django.db import models


class AIFeatureFlag(models.Model):
    """Deliberately minimal — no logic reads this yet. Reserved for a future
    AI feature (e.g. chatbot, content generation) to switch on when built.
    See AI_OPENAI_API_KEY / AI_ANTHROPIC_API_KEY in config/settings.py for
    the matching reserved (currently unused) provider key env slots.
    """

    name = models.CharField(max_length=80, unique=True)
    is_enabled = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "AI xüsusiyyət keçidi"
        verbose_name_plural = "AI xüsusiyyət keçidləri"

    def __str__(self):
        return self.name
