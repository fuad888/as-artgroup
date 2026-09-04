from django.contrib import admin
from modeltranslation.admin import TranslationStackedInline, TranslationAdmin

from .models import AboutContent, Stat


class StatInline(TranslationStackedInline):
    model = Stat
    extra = 0


@admin.register(AboutContent)
class AboutContentAdmin(TranslationAdmin):
    inlines = [StatInline]

    def has_add_permission(self, request):
        return not AboutContent.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
