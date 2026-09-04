from rest_framework import serializers

from contact.models import ContactMessage


class ContactMessageSerializer(serializers.ModelSerializer):
    # phone validation comes from ContactMessage.phone's model-level
    # `validators=[validate_phone]` — ModelSerializer picks it up automatically,
    # so the same rule backs this API and the no-JS ContactMessageForm fallback.
    class Meta:
        model = ContactMessage
        fields = ["id", "name", "email", "phone", "message", "created_at"]
        read_only_fields = ["id", "created_at"]
