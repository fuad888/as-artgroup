from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404, render

from .models import Project


def project_list(request):
    context = {
        "projects": Project.objects.select_related("category").all(),
        "seo_title": _("Layihələr"),
    }
    return render(request, "projects/list.html", context)


def project_detail(request, slug):
    # prefetch_related: the gallery is rendered in full, so without this each
    # item would cost its own query.
    project = get_object_or_404(
        Project.objects.select_related("category").prefetch_related("gallery"), slug=slug
    )
    context = {
        "project": project,
        "seo_title": project.seo_title,
        "seo_description": project.seo_description,
        "seo_image": project.display_image_url,
        "seo_type": "article",
    }
    return render(request, "projects/detail.html", context)
