from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import SeoSettings, ServiceTag, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(TranslationAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SeoSettings)
class SeoSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("İndeksləmə", {"fields": ("allow_indexing",)}),
        ("Paylaşım (Open Graph)", {"fields": ("title_suffix", "default_og_image", "default_og_image_url")}),
        (
            "Analitika",
            {"fields": ("google_analytics_id", "google_tag_manager_id")},
        ),
        (
            "Saytın təsdiqi",
            {"fields": ("google_site_verification", "yandex_verification")},
        ),
    )

    def has_add_permission(self, request):
        return not SeoSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ServiceTag)
class ServiceTagAdmin(TranslationAdmin):
    list_display = ("label", "order")
    list_editable = ("order",)
    ordering = ("order",)
