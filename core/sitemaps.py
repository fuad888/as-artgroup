from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from projects.sitemaps import ProjectSitemap
from team.sitemaps import TeamMemberSitemap


class StaticViewSitemap(Sitemap):
    i18n = True
    alternates = True
    changefreq = "monthly"

    def items(self):
        return [
            "home:page",
            "about:page",
            "equipment:page",
            "projects:list",
            "team:list",
            "contact:page",
        ]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == "home:page" else 0.7


SITEMAPS = {
    "static": StaticViewSitemap,
    "projects": ProjectSitemap,
    "team": TeamMemberSitemap,
}
