from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ContactMessage
from .notifications import notify_new_contact_message


@receiver(post_save, sender=ContactMessage)
def on_contact_message_created(sender, instance, created, **kwargs):
    if not created:
        return
    # Deferred to commit so a rolled-back submission never triggers an email.
    transaction.on_commit(lambda: notify_new_contact_message(instance))
