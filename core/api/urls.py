from django.urls import path

from .views import ServiceTagListView, SiteSettingsDetailView

app_name = "core_api"

urlpatterns = [
    path("site-settings/", SiteSettingsDetailView.as_view(), name="site-settings"),
    path("service-tags/", ServiceTagListView.as_view(), name="service-tags"),
]
