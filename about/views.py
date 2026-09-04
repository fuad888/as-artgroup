from django.utils.translation import gettext_lazy as _
from django.shortcuts import render

from .models import AboutContent


def about_page(request):
    about = AboutContent.load()
    context = {
        "about": about,
        "stats": about.stats.all(),
        "seo_title": _("Haqqımızda"),
        "seo_description": about.lead,
        "seo_image": about.display_image_url,
    }
    return render(request, "about/page.html", context)
