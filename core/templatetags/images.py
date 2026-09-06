from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django import template

register = template.Library()

# Unsplash renders any width from the same photo id, so a single stored URL can
# serve every screen size. Nothing else in the project has a resizing service
# behind it, hence the host check rather than a blanket rewrite.
RESIZABLE_HOST = "images.unsplash.com"
DEFAULT_WIDTHS = (480, 768, 1024, 1440, 1920, 2400)


@register.simple_tag
def responsive_srcset(url, widths=None):
    """A srcset for a resizable image URL, or "" when the URL is not resizable.

    The stored hero URL asks for w=2400: 312 KB pushed to a 393 px phone, and
    the largest contentful paint on the page. With a srcset the browser picks a
    width that matches the device instead.
    """
    if not url or RESIZABLE_HOST not in url:
        return ""

    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query))
    candidates = []
    for width in widths or DEFAULT_WIDTHS:
        query["w"] = str(width)
        candidates.append(f"{urlunsplit(parts._replace(query=urlencode(query)))} {width}w")
    return ", ".join(candidates)
