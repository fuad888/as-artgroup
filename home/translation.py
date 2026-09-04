from modeltranslation.translator import TranslationOptions, register

from .models import HeroContent, HeroFeature


@register(HeroContent)
class HeroContentTranslationOptions(TranslationOptions):
    fields = (
        "eyebrow",
        "heading_line1",
        "heading_line2",
        "heading_line3",
        "lead",
        "cta_primary_label",
        "cta_secondary_label",
    )


@register(HeroFeature)
class HeroFeatureTranslationOptions(TranslationOptions):
    fields = ("title", "description")
