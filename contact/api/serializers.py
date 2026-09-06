from rest_framework import serializers

from contact.models import ContactMessage


class ContactMessageSerializer(serializers.ModelSerializer):
    # Fields are left to ModelSerializer on purpose: it carries the model-level
    # validators across (validate_phone, validate_attachment), so this API and
    # the no-JS ContactMessageForm enforce exactly the same rules. Declaring
    # `attachment` by hand here silently dropped the file-type check.
    class Meta:
        model = ContactMessage
        fields = ["id", "name", "email", "phone", "message", "attachment", "created_at"]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {"attachment": {"required": False}}
