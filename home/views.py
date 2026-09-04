from django.shortcuts import render

from about.models import AboutContent
from contact.forms import ContactMessageForm
from equipment.models import EquipmentCategory
from projects.models import Project
from team.models import TeamMember

from .models import HeroContent


def home(request):
    about = AboutContent.load()
    hero = HeroContent.load()
    context = {
        "hero": hero,
        "hero_features": hero.features.all(),
        "about": about,
        "stats": about.stats.all(),
        "equipment_categories": EquipmentCategory.objects.prefetch_related("tags").all(),
        "featured_projects": Project.objects.select_related("category").filter(is_featured=True),
        "team_members": TeamMember.objects.all(),
        "contact_form": ContactMessageForm(),
    }
    return render(request, "home/home.html", context)
