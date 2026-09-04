from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404, render

from .models import TeamMember


def team_list(request):
    context = {
        "members": TeamMember.objects.all(),
        "seo_title": _("Komanda"),
    }
    return render(request, "team/list.html", context)


def team_detail(request, slug):
    member = get_object_or_404(TeamMember, slug=slug)
    context = {
        "member": member,
        "seo_title": member.seo_title,
        "seo_description": member.seo_description,
        "seo_image": member.display_photo_url,
        "seo_type": "profile",
    }
    return render(request, "team/detail.html", context)
