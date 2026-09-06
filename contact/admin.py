from django.contrib import admin
from django.utils.html import format_html

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "attachment_link", "created_at", "is_handled")
    list_filter = ("is_handled", "created_at")
    search_fields = ("name", "email", "phone", "message")
    date_hierarchy = "created_at"
    list_editable = ("is_handled",)
    # Leads are submitted by visitors — only the triage flag is editable here.
    readonly_fields = ("name", "email", "phone", "message", "attachment", "created_at")

    @admin.display(description="Fayl")
    def attachment_link(self, obj):
        if not obj.attachment:
            return "—"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">{}</a>',
            obj.attachment.url,
            obj.attachment.name.rsplit("/", 1)[-1],
        )

    def has_add_permission(self, request):
        return False
