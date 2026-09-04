from modeltranslation.translator import TranslationOptions, register

from .models import AboutContent, Stat


@register(AboutContent)
class AboutContentTranslationOptions(TranslationOptions):
    fields = (
        "eyebrow",
        "heading",
        "heading_accent",
        "lead",
        "body_paragraph_1",
        "body_paragraph_2",
        "badge_title",
        "badge_subtitle",
        "cta_primary_label",
        "cta_secondary_label",
    )


@register(Stat)
class StatTranslationOptions(TranslationOptions):
    fields = ("label", "description")
