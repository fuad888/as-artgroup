import re
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include("core.seo_urls")),
    path("api/v1/core/", include("core.api.urls")),
    path("api/v1/home/", include("home.api.urls")),
    path("api/v1/about/", include("about.api.urls")),
    path("api/v1/equipment/", include("equipment.api.urls")),
    path("api/v1/projects/", include("projects.api.urls")),
    path("api/v1/team/", include("team.api.urls")),
    path("api/v1/contact/", include("contact.api.urls")),
    path("api/v1/", include("core.api.root_urls")),
]

urlpatterns += i18n_patterns(
    path("", include("home.urls")),
    path("haqqimizda/", include("about.urls")),
    path("avadanliq/", include("equipment.urls")),
    path("layiheler/", include("projects.urls")),
    path("komanda/", include("team.urls")),
    path("elaqe/", include("contact.urls")),
)

# Uploaded files (contact attachments, project galleries) live under MEDIA_ROOT.
# django.conf.urls.static.static() is a no-op unless DEBUG, and this deployment
# has no nginx in front to map the URL, so every upload would 404 in production.
# The route is therefore built explicitly. django.views.static.serve resolves
# through safe_join, so a path cannot escape MEDIA_ROOT. Handing /media/ to the
# web server is faster and stays preferable; this keeps uploads working without it.
urlpatterns += [
    re_path(rf"^{re.escape(settings.MEDIA_URL.strip('/'))}/(?P<path>.*)$", serve,
            {"document_root": settings.MEDIA_ROOT}),
]
