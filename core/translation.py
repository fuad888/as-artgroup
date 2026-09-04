from modeltranslation.translator import TranslationOptions, register

from .models import ServiceTag, SiteSettings


@register(SiteSettings)
class SiteSettingsTranslationOptions(TranslationOptions):
    fields = (
        "site_tagline",
        "meta_description",
        "address_line",
        "address_note",
        "working_hours_line",
        "working_hours_note",
        "footer_note",
        "copyright_text",
    )


@register(ServiceTag)
class ServiceTagTranslationOptions(TranslationOptions):
    fields = ("label",)
