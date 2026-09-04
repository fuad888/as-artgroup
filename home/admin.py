from django.contrib import admin
from modeltranslation.admin import TranslationStackedInline, TranslationAdmin

from .models import HeroContent, HeroFeature


class HeroFeatureInline(TranslationStackedInline):
    model = HeroFeature
    extra = 0


@admin.register(HeroContent)
class HeroContentAdmin(TranslationAdmin):
    inlines = [HeroFeatureInline]

    def has_add_permission(self, request):
        return not HeroContent.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
