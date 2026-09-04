from django.urls import path

from .views import HeroContentDetailView

app_name = "home_api"

urlpatterns = [
    path("hero/", HeroContentDetailView.as_view(), name="hero"),
]
