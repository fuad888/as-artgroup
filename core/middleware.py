"""Response-level fixes that belong to every page rather than a single view."""


class HtmlCacheControlMiddleware:
    """Give HTML pages an explicit caching policy.

    Without a Cache-Control header a browser falls back to heuristic caching and
    may keep serving a stale page long after a deploy — which is exactly how a
    phone ends up running yesterday's JavaScript against today's markup.

    These pages carry a per-request CSRF token, so they are not shareable
    between visitors and cannot be cached by an intermediary at all; "private,
    no-cache" states both facts. The response is still stored locally, it just
    has to be revalidated before reuse.
    """

    HEADER = "private, no-cache, max-age=0, must-revalidate"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # A view that made its own decision (the admin, the API) keeps it.
        if response.has_header("Cache-Control"):
            return response

        if response.get("Content-Type", "").startswith("text/html"):
            response["Cache-Control"] = self.HEADER

        return response
