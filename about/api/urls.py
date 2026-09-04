from django.urls import path

from .views import AboutContentDetailView

app_name = "about_api"

urlpatterns = [
    path("", AboutContentDetailView.as_view(), name="detail"),
]
