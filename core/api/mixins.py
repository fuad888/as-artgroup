from django.conf import settings
from django.utils.cache import patch_cache_control


class PublicCacheMixin:
    """Marks read-only public content as cacheable by browsers and CDNs.

    Content changes only when an admin edits it, so a short shared cache plus
    stale-while-revalidate absorbs traffic spikes without serving stale data for long.
    """

    cache_max_age = 60
    cache_shared_max_age = 300

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if request.method in ("GET", "HEAD") and response.status_code == 200:
            patch_cache_control(
                response,
                public=True,
                max_age=self.cache_max_age,
                s_maxage=self.cache_shared_max_age,
                stale_while_revalidate=60,
            )
        return response


class LanguageScopedSerializerMixin:
    """Serializers return every language by default so machine consumers get one
    payload. `?lang=az` (or ru) drops the other language's fields, roughly halving
    the response for clients that render a single locale.
    """

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        requested = self.request.query_params.get("lang")
        if requested not in dict(settings.LANGUAGES):
            return serializer

        drop = [code for code, _ in settings.LANGUAGES if code != requested]
        target = serializer.child if hasattr(serializer, "child") else serializer
        self._prune(target, drop)
        return serializer

    def _prune(self, serializer, drop):
        for name in list(serializer.fields):
            if any(name.endswith(f"_{code}") for code in drop):
                serializer.fields.pop(name)
                continue
            nested = serializer.fields[name]
            nested = getattr(nested, "child", nested)
            if hasattr(nested, "fields"):
                self._prune(nested, drop)
