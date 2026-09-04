from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import ContactMessageForm


def contact_page(request):
    context = {
        "form": ContactMessageForm(),
        "seo_title": _("Əlaqə"),
    }
    return render(request, "contact/page.html", context)


def contact_submit(request):
    """No-JS progressive-enhancement fallback. The primary submission path is
    the JS fetch() call against /api/v1/contact/messages/."""
    if request.method == "POST":
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Təşəkkürlər! Sorğunuz qeydə alındı — komandamız tezliklə sizinlə əlaqə saxlayacaq.",
            )
        else:
            messages.error(request, "Zəhmət olmasa bütün sahələri düzgün doldurun.")
    return redirect(reverse("contact:page"))
