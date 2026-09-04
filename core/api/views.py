from rest_framework.generics import ListAPIView, RetrieveAPIView

from core.api.mixins import LanguageScopedSerializerMixin, PublicCacheMixin

from core.models import ServiceTag, SiteSettings

from .serializers import ServiceTagSerializer, SiteSettingsSerializer


class SiteSettingsDetailView(PublicCacheMixin, LanguageScopedSerializerMixin, RetrieveAPIView):
    serializer_class = SiteSettingsSerializer

    def get_object(self):
        return SiteSettings.load()


class ServiceTagListView(PublicCacheMixin, LanguageScopedSerializerMixin, ListAPIView):
    queryset = ServiceTag.objects.all()
    serializer_class = ServiceTagSerializer
    pagination_class = None
