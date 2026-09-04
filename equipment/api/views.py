from rest_framework.generics import ListAPIView

from core.api.mixins import LanguageScopedSerializerMixin, PublicCacheMixin

from equipment.models import EquipmentCategory

from .serializers import EquipmentCategorySerializer


class EquipmentCategoryListView(PublicCacheMixin, LanguageScopedSerializerMixin, ListAPIView):
    queryset = EquipmentCategory.objects.prefetch_related("tags").all()
    serializer_class = EquipmentCategorySerializer
    pagination_class = None
