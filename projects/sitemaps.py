from django.contrib.sitemaps import Sitemap

from .models import Project


class ProjectSitemap(Sitemap):
    i18n = True
    alternates = True
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return Project.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        return obj.updated_at
