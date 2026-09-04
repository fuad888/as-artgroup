from rest_framework import serializers

from core.api.fields import AbsoluteURLField

from team.models import TeamMember


class TeamMemberListSerializer(serializers.ModelSerializer):
    display_photo_url = AbsoluteURLField()

    class Meta:
        model = TeamMember
        fields = [
            "id",
            "name",
            "slug",
            "role_az",
            "role_ru",
            "display_photo_url",
            "linkedin_url",
            "instagram_url",
            "order",
        ]


class TeamMemberDetailSerializer(TeamMemberListSerializer):
    class Meta(TeamMemberListSerializer.Meta):
        fields = TeamMemberListSerializer.Meta.fields + ["bio_az", "bio_ru"]
