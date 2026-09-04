from rest_framework import serializers

from core.api.fields import AbsoluteURLField

from projects.models import Project, ProjectCategory


class ProjectCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCategory
        fields = ["id", "name_az", "name_ru", "slug"]


class ProjectListSerializer(serializers.ModelSerializer):
    category = ProjectCategorySerializer(read_only=True)
    display_image_url = AbsoluteURLField()

    class Meta:
        model = Project
        fields = [
            "id",
            "title_az",
            "title_ru",
            "slug",
            "category",
            "display_image_url",
            "meta_primary_az",
            "meta_primary_ru",
            "meta_secondary_az",
            "meta_secondary_ru",
            "is_featured",
            "gradient_key",
            "order",
        ]


class ProjectDetailSerializer(ProjectListSerializer):
    class Meta(ProjectListSerializer.Meta):
        fields = ProjectListSerializer.Meta.fields + ["description_az", "description_ru"]
