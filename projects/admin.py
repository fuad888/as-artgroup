from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import Project, ProjectCategory


# Slugs are generated server-side by az_slugify (admin's prepopulated_fields JS
# mangles Azerbaijani letters); leave the field empty to auto-fill it.
@admin.register(ProjectCategory)
class ProjectCategoryAdmin(TranslationAdmin):
    list_display = ("name", "slug")


@admin.register(Project)
class ProjectAdmin(TranslationAdmin):
    list_display = ("title", "category", "is_featured", "order")
    list_filter = ("category", "is_featured")
    list_editable = ("order",)
    ordering = ("order",)
