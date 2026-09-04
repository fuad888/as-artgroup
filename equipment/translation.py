from modeltranslation.translator import TranslationOptions, register

from .models import EquipmentCategory, EquipmentTag


@register(EquipmentCategory)
class EquipmentCategoryTranslationOptions(TranslationOptions):
    fields = ("tag_label", "title", "description")


@register(EquipmentTag)
class EquipmentTagTranslationOptions(TranslationOptions):
    fields = ("label",)
