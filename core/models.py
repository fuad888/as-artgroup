from urllib.parse import quote

from django.conf import settings
from django.core.cache import cache
from django.core.validators import RegexValidator
from django.db import models


class SingletonModel(models.Model):
    """Base class for models that must have exactly one row (pk=1).

    These rows are read on nearly every request but change only when an admin
    edits them, so `load()` is cached and the cache is dropped on save.
    """

    id = models.PositiveIntegerField(primary_key=True, default=1, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.id = 1
        super().save(*args, **kwargs)
        cache.delete(self.cache_key())

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def cache_key(cls):
        return f"singleton:{cls._meta.label_lower}"

    @classmethod
    def load(cls):
        key = cls.cache_key()
        obj = cache.get(key)
        if obj is None:
            obj, _ = cls.objects.get_or_create(id=1)
            cache.set(key, obj, settings.CACHE_TTL_SETTINGS)
        return obj


class SiteSettings(SingletonModel):
    site_name = models.CharField(max_length=120, default="AS-ART Group")
    site_tagline = models.CharField(max_length=255, blank=True)
    logo_mark_text = models.CharField(max_length=10, default="AS")
    meta_description = models.TextField(blank=True)

    phone = models.CharField(max_length=32, blank=True, help_text="Əsas mobil nömrə")
    office_phone = models.CharField(max_length=32, blank=True, help_text="Ofis (stasionar) nömrəsi")
    whatsapp_phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    booking_email = models.EmailField(blank=True)

    address_line = models.CharField(max_length=255, blank=True)
    address_note = models.CharField(max_length=255, blank=True)
    map_query = models.CharField(
        max_length=255,
        blank=True,
        help_text="Naviqasiya tətbiqlərinə göndərilən ünvan/koordinat. "
        "Boş buraxılsa ünvan sətri istifadə olunur.",
    )
    working_hours_line = models.CharField(max_length=255, blank=True)
    working_hours_note = models.CharField(max_length=255, blank=True)
    map_embed_url = models.URLField(blank=True)

    footer_note = models.CharField(max_length=255, blank=True)
    copyright_text = models.CharField(max_length=255, blank=True)

    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "Sayt tənzimləmələri"
        verbose_name_plural = "Sayt tənzimləmələri"

    def __str__(self):
        return self.site_name

    @staticmethod
    def _dial(number):
        """Strip spaces/brackets so tel: links dial exactly what was typed."""
        if not number:
            return ""
        kept = "".join(ch for ch in number if ch.isdigit() or ch == "+")
        return kept

    @property
    def phone_href(self):
        return f"tel:{self._dial(self.phone)}" if self.phone else ""

    @property
    def office_phone_href(self):
        return f"tel:{self._dial(self.office_phone)}" if self.office_phone else ""

    @property
    def whatsapp_href(self):
        # wa.me expects digits only, no plus sign.
        digits = self._dial(self.whatsapp_phone).lstrip("+")
        return f"https://wa.me/{digits}" if digits else ""

    @property
    def email_href(self):
        return f"mailto:{self.email}" if self.email else ""

    @property
    def booking_email_href(self):
        return f"mailto:{self.booking_email}" if self.booking_email else ""

    @property
    def map_destination(self):
        return self.map_query or self.address_line

    @property
    def maps_href(self):
        """Universal link: opens the maps app on mobile, the browser on desktop.
        site.js upgrades this to a geo: URI on Android so the OS offers every
        installed navigation app."""
        if not self.map_destination:
            return ""
        return "https://www.google.com/maps/search/?api=1&query=" + quote(self.map_destination)


class SeoSettings(SingletonModel):
    title_suffix = models.CharField(
        max_length=80,
        blank=True,
        default="AS-ART Group",
        help_text='Səhifə başlığının sonuna əlavə olunur: "Layihələr | AS-ART Group"',
    )
    default_og_image = models.ImageField(upload_to="seo/", blank=True)
    default_og_image_url = models.URLField(blank=True)

    allow_indexing = models.BooleanField(
        default=False,
        help_text="Sayt hazır olanda aktivləşdirin. Söndürülü ikən robots.txt bütün "
        "axtarış robotlarını bloklayır (hazırlıq mərhələsində indekslənməmək üçün).",
    )

    google_analytics_id = models.CharField(
        max_length=40,
        blank=True,
        validators=[RegexValidator(r"^G-[A-Z0-9]{6,12}$", "GA4 formatı: G-XXXXXXXXXX")],
        help_text="GA4 Measurement ID, məs. G-ABCD123456",
    )
    google_tag_manager_id = models.CharField(
        max_length=40,
        blank=True,
        validators=[RegexValidator(r"^GTM-[A-Z0-9]{5,10}$", "GTM formatı: GTM-XXXXXXX")],
        help_text="Google Tag Manager ID, məs. GTM-ABC1234 (GA4 ilə birlikdə lazım deyil)",
    )
    google_site_verification = models.CharField(
        max_length=120, blank=True, help_text="Google Search Console təsdiq kodu"
    )
    yandex_verification = models.CharField(
        max_length=120, blank=True, help_text="Yandex Webmaster təsdiq kodu"
    )

    class Meta:
        verbose_name = "SEO və Analitika"
        verbose_name_plural = "SEO və Analitika"

    def __str__(self):
        return "SEO və Analitika"

    @property
    def display_og_image_url(self):
        return self.default_og_image.url if self.default_og_image else self.default_og_image_url


class ServiceTag(models.Model):
    """Feeds both the homepage marquee strip and the footer 'Xidmətlər' column."""

    label = models.CharField(max_length=80)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Xidmət"
        verbose_name_plural = "Xidmətlər"

    def __str__(self):
        return self.label
