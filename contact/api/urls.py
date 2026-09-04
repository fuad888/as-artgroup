from django.urls import path

from .views import ContactMessageCreateView

app_name = "contact_api"

urlpatterns = [
    path("messages/", ContactMessageCreateView.as_view(), name="messages-create"),
]
