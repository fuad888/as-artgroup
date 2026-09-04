from django.contrib import admin
from modeltranslation.admin import TranslationStackedInline, TranslationAdmin

from .models import EquipmentCategory, EquipmentTag


class EquipmentTagInline(TranslationStackedInline):
    model = EquipmentTag
    extra = 0


@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(TranslationAdmin):
    list_display = ("tag_number", "title", "order")
    list_editable = ("order",)
    ordering = ("order",)
    inlines = [EquipmentTagInline]
