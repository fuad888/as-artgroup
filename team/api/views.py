from rest_framework.generics import ListAPIView, RetrieveAPIView

from core.api.mixins import LanguageScopedSerializerMixin, PublicCacheMixin

from team.models import TeamMember

from .serializers import TeamMemberDetailSerializer, TeamMemberListSerializer


class TeamMemberListView(PublicCacheMixin, LanguageScopedSerializerMixin, ListAPIView):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberListSerializer
    pagination_class = None


class TeamMemberDetailView(PublicCacheMixin, LanguageScopedSerializerMixin, RetrieveAPIView):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberDetailSerializer
    lookup_field = "slug"
