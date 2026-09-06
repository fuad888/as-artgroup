from django.contrib import admin
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline

from .models import Project, ProjectCategory, ProjectMedia


# Slugs are generated server-side by az_slugify (admin's prepopulated_fields JS
# mangles Azerbaijani letters); leave the field empty to auto-fill it.
@admin.register(ProjectCategory)
class ProjectCategoryAdmin(TranslationAdmin):
    list_display = ("name", "slug")


class ProjectMediaInline(TranslationTabularInline):
    """Edited inside the project it belongs to — a gallery item has no meaning
    on its own, so it gets no separate admin entry."""

    model = ProjectMedia
    extra = 1
    fields = ("kind", "image", "image_url", "video", "video_url", "caption", "order")


@admin.register(Project)
class ProjectAdmin(TranslationAdmin):
    list_display = ("title", "category", "gallery_count", "is_featured", "order")
    list_filter = ("category", "is_featured")
    list_editable = ("order",)
    ordering = ("order",)
    inlines = [ProjectMediaInline]

    @admin.display(description="Qalereya")
    def gallery_count(self, obj):
        return obj.gallery.count()
