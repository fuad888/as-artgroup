import json

from django import template
from django.urls import translate_url
from django.utils.safestring import mark_safe

register = template.Library()

# Same escaping Django's json_script applies, so the payload can never break
# out of the surrounding <script> tag.
_JSON_SCRIPT_ESCAPES = {ord("<"): "\\u003C", ord(">"): "\\u003E", ord("&"): "\\u0026"}


@register.simple_tag(takes_context=True)
def alternate_url(context, language_code):
    """Current page's URL under another language prefix — used for hreflang
    alternates and the header language switcher."""
    request = context.get("request")
    if request is None:
        return ""
    return translate_url(request.get_full_path(), language_code)


@register.simple_tag(takes_context=True)
def canonical_url(context):
    request = context.get("request")
    if request is None:
        return ""
    return request.build_absolute_uri(request.path)


@register.simple_tag(takes_context=True)
def organization_schema(context):
    """Organization JSON-LD so Google can render a knowledge panel / rich result."""
    request = context.get("request")
    site_settings = context.get("site_settings")
    seo_settings = context.get("seo_settings")
    if request is None or site_settings is None:
        return ""

    social_links = [
        url
        for url in (
            site_settings.instagram_url,
            site_settings.facebook_url,
            site_settings.linkedin_url,
            site_settings.youtube_url,
        )
        if url
    ]

    data = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": site_settings.site_name,
        "url": request.build_absolute_uri("/"),
        "description": site_settings.meta_description,
    }
    if seo_settings is not None and seo_settings.display_og_image_url:
        data["logo"] = request.build_absolute_uri(seo_settings.display_og_image_url)
    if site_settings.phone:
        data["telephone"] = site_settings.phone
    if site_settings.email:
        data["email"] = site_settings.email
    if site_settings.address_line:
        data["address"] = {
            "@type": "PostalAddress",
            "streetAddress": site_settings.address_line,
            "addressLocality": "Bakı",
            "addressCountry": "AZ",
        }
    if social_links:
        data["sameAs"] = social_links

    return mark_safe(json.dumps(data, ensure_ascii=False).translate(_JSON_SCRIPT_ESCAPES))
