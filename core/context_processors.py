from django.conf import settings

from .models import SeoSettings, ServiceTag, SiteSettings


def site(request):
    """Site-wide chrome, SEO defaults and analytics IDs for every template."""
    return {
        "site_settings": SiteSettings.load(),
        "seo_settings": SeoSettings.load(),
        # Footer column and homepage marquee read from the same list.
        "service_tags": ServiceTag.objects.all(),
        # Never send local development traffic to production analytics.
        "analytics_enabled": not settings.DEBUG,
    }
