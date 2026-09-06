"""One submission limit shared by both ways a visitor can send the form.

The JS path posts to the DRF endpoint, which DRF throttles. The no-JS form
posts to a plain Django view, which DRF never sees — so without this the limit
was trivially bypassed by posting straight to /elaqe/submit/. Both paths now
count against the same cache key.
"""

from rest_framework.throttling import AnonRateThrottle


class ContactThrottle(AnonRateThrottle):
    scope = "contact"


def submission_allowed(request):
    """True when this client may submit again. Shares DRF's counter, so five
    submissions through the API leave none for the plain form."""
    throttle = ContactThrottle()
    # AnonRateThrottle keys on the client IP and reads only request.META,
    # which a plain HttpRequest provides.
    return throttle.allow_request(request, None)
