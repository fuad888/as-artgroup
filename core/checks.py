"""Deploy-time checks for settings that live in the database rather than in
settings.py, and so are invisible to Django's own --deploy checks."""

from django.conf import settings
from django.core.checks import Warning, register


@register(deploy=True)
def indexing_should_be_on_in_production(app_configs, **kwargs):
    """SeoSettings.allow_indexing ships off so a half-built site is never
    crawled. The cost of that default is that nothing complains when a finished
    site goes live still invisible to Google — no error, no broken page, just
    no traffic. This turns it into a line in `manage.py check --deploy`.
    """
    if settings.DEBUG:
        return []

    try:
        from core.models import SeoSettings

        if SeoSettings.load().allow_indexing:
            return []
    except Exception:
        # No database yet (a first deploy, before migrate) — nothing to judge.
        return []

    return [
        Warning(
            "Axtarış sistemləri üçün indeksləmə söndürülüdür.",
            hint=(
                "Sayt hazırdırsa, admin paneldə açın: "
                "/admin/core/seosettings/ -> İndeksləmə -> Allow indexing. "
                "Söndürülü ikən hər səhifə 'noindex, nofollow' verir və "
                "robots.txt bütün robotları bloklayır."
            ),
            id="core.W001",
        )
    ]
