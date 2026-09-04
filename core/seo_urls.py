from django.contrib.sitemaps.views import sitemap
from django.urls import path

from .sitemaps import SITEMAPS
from .views import robots_txt

urlpatterns = [
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots"),
]
