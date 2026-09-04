from django.http import HttpResponse
from django.urls import reverse

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
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")
