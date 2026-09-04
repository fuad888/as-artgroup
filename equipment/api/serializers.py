from rest_framework import serializers

from core.api.fields import AbsoluteURLField

from equipment.models import EquipmentCategory, EquipmentTag


class EquipmentTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentTag
        fields = ["id", "label_az", "label_ru", "order"]


class EquipmentCategorySerializer(serializers.ModelSerializer):
    tags = EquipmentTagSerializer(many=True, read_only=True)
    display_image_url = AbsoluteURLField()

    class Meta:
        model = EquipmentCategory
        fields = [
            "id",
            "tag_number",
            "tag_label_az",
            "tag_label_ru",
            "title_az",
            "title_ru",
            "description_az",
            "description_ru",
            "display_image_url",
            "gradient_key",
            "order",
            "tags",
        ]
