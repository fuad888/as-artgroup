from rest_framework.generics import CreateAPIView
from rest_framework.throttling import AnonRateThrottle

from .serializers import ContactMessageSerializer


class ContactThrottle(AnonRateThrottle):
    scope = "contact"


class ContactMessageCreateView(CreateAPIView):
    serializer_class = ContactMessageSerializer
    throttle_classes = [ContactThrottle]
