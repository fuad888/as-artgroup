from django.contrib.sitemaps.views import sitemap
from django.templatetags.static import static
from django.urls import path
from django.views.decorators.cache import cache_control
from django.views.generic.base import RedirectView

from .sitemaps import SITEMAPS
from .views import robots_txt

urlpatterns = [
    # Crawlers refetch the sitemap often; it only changes when content does.
    path(
        "sitemap.xml",
        cache_control(public=True, max_age=300, s_maxage=3600)(sitemap),
        {"sitemaps": SITEMAPS},
        name="sitemap",
    ),
    path("robots.txt", robots_txt, name="robots"),
    # Browsers and crawlers request /favicon.ico directly, regardless of the
    # <link rel="icon"> in the page; without this they get a 404.
    path(
        "favicon.ico",
        RedirectView.as_view(url=static("favicon.ico"), permanent=True),
        name="favicon",
    ),
]
