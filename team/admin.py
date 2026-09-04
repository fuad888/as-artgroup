from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import TeamMember


# Slug is generated server-side by az_slugify; leave it empty to auto-fill.
@admin.register(TeamMember)
class TeamMemberAdmin(TranslationAdmin):
    list_display = ("name", "role", "order")
    list_editable = ("order",)
    ordering = ("order",)
