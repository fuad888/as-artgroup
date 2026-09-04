from django.urls import path

from .root import api_root

urlpatterns = [
    path("", api_root, name="api-root"),
]
