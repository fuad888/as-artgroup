from django_filters import rest_framework as filters
from rest_framework.generics import ListAPIView, RetrieveAPIView

from core.api.mixins import LanguageScopedSerializerMixin, PublicCacheMixin

from projects.models import Project

from .serializers import ProjectDetailSerializer, ProjectListSerializer


class ProjectFilter(filters.FilterSet):
    category = filters.CharFilter(field_name="category__slug")

    class Meta:
        model = Project
        fields = ["category", "is_featured"]


class ProjectListView(PublicCacheMixin, LanguageScopedSerializerMixin, ListAPIView):
    queryset = Project.objects.select_related("category").all()
    serializer_class = ProjectListSerializer
    filterset_class = ProjectFilter


class ProjectDetailView(PublicCacheMixin, LanguageScopedSerializerMixin, RetrieveAPIView):
    queryset = Project.objects.select_related("category").all()
    serializer_class = ProjectDetailSerializer
    lookup_field = "slug"
