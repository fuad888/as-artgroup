from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(["GET"])
def api_root(request, format=None):
    """Entry point listing every public endpoint, so a future frontend or AI
    consumer can discover the API without reading the source."""
    return Response(
        {
            "site-settings": reverse("core_api:site-settings", request=request, format=format),
            "service-tags": reverse("core_api:service-tags", request=request, format=format),
            "hero": reverse("home_api:hero", request=request, format=format),
            "about": reverse("about_api:detail", request=request, format=format),
            "equipment-categories": reverse("equipment_api:categories", request=request, format=format),
            "projects": reverse("projects_api:list", request=request, format=format),
            "team": reverse("team_api:list", request=request, format=format),
            "contact-messages": reverse("contact_api:messages-create", request=request, format=format),
        }
    )
