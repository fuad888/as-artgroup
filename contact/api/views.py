from rest_framework.generics import CreateAPIView

from contact.throttling import ContactThrottle

from .serializers import ContactMessageSerializer


class ContactMessageCreateView(CreateAPIView):
    serializer_class = ContactMessageSerializer
    throttle_classes = [ContactThrottle]
