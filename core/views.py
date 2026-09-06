from django.http import HttpResponse
from django.urls import reverse
from django.utils.cache import patch_cache_control

from .models import SeoSettings


def robots_txt(request):
    seo = SeoSettings.load()
    if not seo.allow_indexing:
        # Pre-launch default: keep the whole site out of search results until
        # an admin turns indexing on in SEO və Analitika.
        lines = ["User-agent: *", "Disallow: /"]
    else:
        sitemap_url = request.build_absolute_uri(reverse("sitemap"))
        lines = [
            "User-agent: *",
            "Disallow: /admin/",
            "Disallow: /api/",
            "",
            f"Sitemap: {sitemap_url}",
        ]
    response = HttpResponse("\n".join(lines) + "\n", content_type="text/plain")
    # Crawlers refetch this constantly and it changes only when an admin flips
    # the indexing switch; an hour at the edge costs nothing and saves a render.
    patch_cache_control(response, public=True, max_age=300, s_maxage=3600)
    return response
