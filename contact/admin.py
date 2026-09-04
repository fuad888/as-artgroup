from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "created_at", "is_handled")
    list_filter = ("is_handled", "created_at")
    search_fields = ("name", "email", "phone", "message")
    date_hierarchy = "created_at"
    list_editable = ("is_handled",)
    # Leads are submitted by visitors — only the triage flag is editable here.
    readonly_fields = ("name", "email", "phone", "message", "created_at")

    def has_add_permission(self, request):
        return False
