import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse

logger = logging.getLogger(__name__)


def notification_recipients():
    """Explicit override wins; otherwise the address shown on the site."""
    if settings.CONTACT_NOTIFY_EMAIL:
        return [settings.CONTACT_NOTIFY_EMAIL]

    from core.models import SiteSettings

    site_email = SiteSettings.load().email
    return [site_email] if site_email else []


def _single_line(value):
    """A mail subject is one line by definition. Collapsing newlines both blocks
    header injection and keeps the notification sendable instead of dropped."""
    return " ".join(str(value or "").split())


def build_notification(instance):
    admin_path = reverse("admin:contact_contactmessage_change", args=[instance.pk])
    body = "\n".join(
        [
            "Saytdan yeni əlaqə sorğusu:",
            "",
            f"Ad:      {instance.name}",
            f"Email:   {instance.email}",
            f"Telefon: {instance.phone}",
            f"Tarix:   {instance.created_at:%d.%m.%Y %H:%M}",
            "",
            "Mesaj:",
            instance.message,
            "",
            f"Admin paneldə: {admin_path}",
        ]
    )
    message = EmailMessage(
        subject=_single_line(f"Yeni əlaqə sorğusu — {instance.name}"),
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=notification_recipients(),
        # Replying in the mail client answers the customer directly.
        reply_to=[instance.email] if instance.email else None,
    )
    return message


def notify_new_contact_message(instance):
    """The lead is already saved before this runs, so a mail failure only costs
    the notification — never the submission itself."""
    logger.info("New contact message from %s <%s>", instance.name, instance.email)

    recipients = notification_recipients()
    if not recipients:
        logger.warning("No contact notification recipient configured; email skipped")
        return

    try:
        sent = build_notification(instance).send(fail_silently=True)
    except Exception:
        # Mail is a boundary with an external system; the lead is already stored,
        # so nothing here may bubble up and fail the visitor's request.
        logger.exception("Contact notification to %s raised", ", ".join(recipients))
        return

    if sent:
        logger.info("Contact notification sent to %s", ", ".join(recipients))
    else:
        logger.error("Contact notification to %s could not be sent", ", ".join(recipients))
