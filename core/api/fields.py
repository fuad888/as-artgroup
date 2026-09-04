from rest_framework import serializers


class AbsoluteURLField(serializers.ReadOnlyField):
    """Uploaded media resolves to a relative path (/media/...); API consumers
    need a usable absolute URL. External URLs pass through untouched."""

    def to_representation(self, value):
        if not value:
            return ""
        request = self.context.get("request")
        if request is not None and value.startswith("/"):
            return request.build_absolute_uri(value)
        return value
