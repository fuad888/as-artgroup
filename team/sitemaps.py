from django.contrib.sitemaps import Sitemap

from .models import TeamMember


class TeamMemberSitemap(Sitemap):
    i18n = True
    alternates = True
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return TeamMember.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        return obj.updated_at
