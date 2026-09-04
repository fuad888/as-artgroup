from django.contrib import admin

from .models import AIFeatureFlag


@admin.register(AIFeatureFlag)
class AIFeatureFlagAdmin(admin.ModelAdmin):
    list_display = ("name", "is_enabled")
    list_editable = ("is_enabled",)
