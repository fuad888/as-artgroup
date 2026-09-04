from django.utils.translation import gettext_lazy as _
from django.shortcuts import render

from .models import EquipmentCategory


def equipment_page(request):
    context = {
        "categories": EquipmentCategory.objects.prefetch_related("tags").all(),
        "seo_title": _("Avadanlıqlar"),
    }
    return render(request, "equipment/page.html", context)
