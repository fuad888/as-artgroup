from modeltranslation.translator import TranslationOptions, register

from .models import Project, ProjectCategory, ProjectMedia


@register(ProjectCategory)
class ProjectCategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Project)
class ProjectTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "meta_primary",
        "meta_secondary",
        "description",
        "meta_title",
        "meta_description",
    )


@register(ProjectMedia)
class ProjectMediaTranslationOptions(TranslationOptions):
    fields = ("caption",)
