from rest_framework.generics import RetrieveAPIView

from core.api.mixins import LanguageScopedSerializerMixin, PublicCacheMixin

from home.models import HeroContent

from .serializers import HeroContentSerializer


class HeroContentDetailView(PublicCacheMixin, LanguageScopedSerializerMixin, RetrieveAPIView):
    serializer_class = HeroContentSerializer

    def get_object(self):
        return HeroContent.load()
