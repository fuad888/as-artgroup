from rest_framework.generics import RetrieveAPIView

from core.api.mixins import LanguageScopedSerializerMixin, PublicCacheMixin

from about.models import AboutContent

from .serializers import AboutContentSerializer


class AboutContentDetailView(PublicCacheMixin, LanguageScopedSerializerMixin, RetrieveAPIView):
    serializer_class = AboutContentSerializer

    def get_object(self):
        return AboutContent.load()
