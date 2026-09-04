from rest_framework import serializers

from core.api.fields import AbsoluteURLField

from home.models import HeroContent, HeroFeature


class HeroFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroFeature
        fields = ["id", "icon_key", "title_az", "title_ru", "description_az", "description_ru", "order"]


class HeroContentSerializer(serializers.ModelSerializer):
    features = HeroFeatureSerializer(many=True, read_only=True)
    display_image_url = AbsoluteURLField()

    class Meta:
        model = HeroContent
        fields = [
            "eyebrow_az",
            "eyebrow_ru",
            "heading_line1_az",
            "heading_line1_ru",
            "heading_line2_az",
            "heading_line2_ru",
            "heading_line3_az",
            "heading_line3_ru",
            "lead_az",
            "lead_ru",
            "cta_primary_label_az",
            "cta_primary_label_ru",
            "cta_secondary_label_az",
            "cta_secondary_label_ru",
            "display_image_url",
            "features",
        ]
