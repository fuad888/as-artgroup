from rest_framework import serializers

from core.models import ServiceTag, SiteSettings


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = [
            "site_name",
            "site_tagline_az",
            "site_tagline_ru",
            "logo_mark_text",
            "meta_description_az",
            "meta_description_ru",
            "phone",
            "whatsapp_phone",
            "email",
            "booking_email",
            "address_line_az",
            "address_line_ru",
            "address_note_az",
            "address_note_ru",
            "working_hours_line_az",
            "working_hours_line_ru",
            "working_hours_note_az",
            "working_hours_note_ru",
            "map_embed_url",
            "footer_note_az",
            "footer_note_ru",
            "copyright_text_az",
            "copyright_text_ru",
            "instagram_url",
            "facebook_url",
            "linkedin_url",
            "youtube_url",
        ]


class ServiceTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceTag
        fields = ["id", "label_az", "label_ru", "order"]
