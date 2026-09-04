from django.utils.text import slugify

AZ_TRANSLITERATION = str.maketrans(
    {
        "ə": "e", "Ə": "E",
        "ğ": "g", "Ğ": "G",
        "ı": "i", "İ": "I",
        "ö": "o", "Ö": "O",
        "ü": "u", "Ü": "U",
        "ş": "s", "Ş": "S",
        "ç": "c", "Ç": "C",
    }
)


def az_slugify(value):
    """Django's slugify() silently drops Azerbaijani letters that have no ASCII
    decomposition, turning "Yay Səhnəsi Açılışı" into "yay-shnsi-acls".
    Transliterating first keeps slugs readable.
    """
    return slugify((value or "").translate(AZ_TRANSLITERATION))


def unique_slug(instance, value, slug_field="slug"):
    base = az_slugify(value) or "n-a"
    queryset = instance.__class__.objects.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    slug, counter = base, 2
    while queryset.filter(**{slug_field: slug}).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug
