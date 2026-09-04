from rest_framework import serializers

from core.api.fields import AbsoluteURLField

from about.models import AboutContent, Stat


class StatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stat
        fields = [
            "id",
            "number",
            "suffix",
            "label_az",
            "label_ru",
            "description_az",
            "description_ru",
            "gradient_key",
            "order",
        ]


class AboutContentSerializer(serializers.ModelSerializer):
    stats = StatSerializer(many=True, read_only=True)
    display_image_url = AbsoluteURLField()

    class Meta:
        model = AboutContent
        fields = [
            "eyebrow_az",
            "eyebrow_ru",
            "heading_az",
            "heading_ru",
            "heading_accent_az",
            "heading_accent_ru",
            "lead_az",
            "lead_ru",
            "body_paragraph_1_az",
            "body_paragraph_1_ru",
            "body_paragraph_2_az",
            "body_paragraph_2_ru",
            "display_image_url",
            "badge_title_az",
            "badge_title_ru",
            "badge_subtitle_az",
            "badge_subtitle_ru",
            "cta_primary_label_az",
            "cta_primary_label_ru",
            "cta_secondary_label_az",
            "cta_secondary_label_ru",
            "stats",
        ]
