from modeltranslation.translator import TranslationOptions, register

from .models import TeamMember


@register(TeamMember)
class TeamMemberTranslationOptions(TranslationOptions):
    fields = ("role", "bio", "meta_title", "meta_description")
