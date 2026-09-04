from io import StringIO

from django.core.management import call_command
from django.test import RequestFactory, TestCase

from core.testing import BaseTestCase

from core.api.fields import AbsoluteURLField

from about.models import Stat
from core.models import ServiceTag, SiteSettings
from core.utils import az_slugify, unique_slug
from equipment.models import EquipmentCategory, EquipmentTag
from home.models import HeroFeature
from projects.models import Project, ProjectCategory
from team.models import TeamMember


class AzSlugifyTests(BaseTestCase):
    def test_transliterates_azerbaijani_letters(self):
        self.assertEqual(az_slugify("Yay Səhnəsi Açılışı"), "yay-sehnesi-acilisi")
        self.assertEqual(az_slugify("Günel Xəlilova"), "gunel-xelilova")
        self.assertEqual(az_slugify("Şəhər Işıqları"), "seher-isiqlari")
        self.assertEqual(az_slugify("Rəşad Quliyev"), "resad-quliyev")

    def test_empty_value_is_safe(self):
        self.assertEqual(az_slugify(""), "")
        self.assertEqual(az_slugify(None), "")

    def test_unique_slug_appends_counter_on_collision(self):
        category = ProjectCategory.objects.create(name="Konsert")
        first = Project.objects.create(title="Səhnə", category=category)
        second = Project.objects.create(title="Səhnə", category=category)
        self.assertEqual(first.slug, "sehne")
        self.assertEqual(second.slug, "sehne-2")

    def test_unique_slug_ignores_own_row_on_update(self):
        category = ProjectCategory.objects.create(name="Konsert")
        project = Project.objects.create(title="Səhnə", category=category)
        self.assertEqual(unique_slug(project, "Səhnə"), "sehne")


class SingletonModelTests(BaseTestCase):
    def test_load_creates_and_reuses_single_row(self):
        first = SiteSettings.load()
        second = SiteSettings.load()
        self.assertEqual(first.pk, 1)
        self.assertEqual(second.pk, 1)
        self.assertEqual(SiteSettings.objects.count(), 1)

    def test_save_always_forces_pk_one(self):
        settings_obj = SiteSettings(site_name="Test")
        settings_obj.save()
        self.assertEqual(settings_obj.pk, 1)
        self.assertEqual(SiteSettings.objects.count(), 1)

    def test_delete_is_a_no_op(self):
        settings_obj = SiteSettings.load()
        settings_obj.delete()
        self.assertEqual(SiteSettings.objects.count(), 1)


class ContactLinkTests(BaseTestCase):
    """Tap-to-act links: call, WhatsApp chat, mail app, navigation app."""

    def setUp(self):
        super().setUp()
        self.settings_obj = SiteSettings.load()
        self.settings_obj.phone = "+994 51 555 77 44"
        self.settings_obj.office_phone = "+994 12 310 34 35"
        self.settings_obj.whatsapp_phone = "+994 51 555 77 44"
        self.settings_obj.email = "office@as-artgroup.az"
        self.settings_obj.booking_email = "booking@as-artgroup.az"
        self.settings_obj.address_line = "Cəfər Cabbarlı 40, Caspian Business Center AZ1065"
        self.settings_obj.save()

    def test_phone_links_dial_without_formatting(self):
        self.assertEqual(self.settings_obj.phone_href, "tel:+994515557744")
        self.assertEqual(self.settings_obj.office_phone_href, "tel:+994123103435")

    def test_phone_link_strips_brackets_and_dashes(self):
        self.settings_obj.phone = "(012) 310-34-35"
        self.assertEqual(self.settings_obj.phone_href, "tel:0123103435")

    def test_whatsapp_link_uses_wa_me_without_plus(self):
        self.assertEqual(self.settings_obj.whatsapp_href, "https://wa.me/994515557744")

    def test_email_links_are_mailto(self):
        self.assertEqual(self.settings_obj.email_href, "mailto:office@as-artgroup.az")
        self.assertEqual(self.settings_obj.booking_email_href, "mailto:booking@as-artgroup.az")

    def test_map_link_encodes_the_destination(self):
        self.settings_obj.map_query = "Caspian Business Center, Baku"
        href = self.settings_obj.maps_href
        self.assertTrue(href.startswith("https://www.google.com/maps/search/?api=1&query="))
        self.assertIn("Caspian%20Business%20Center", href)

    def test_map_destination_falls_back_to_the_address(self):
        self.settings_obj.map_query = ""
        self.assertEqual(self.settings_obj.map_destination, self.settings_obj.address_line)

    def test_blank_values_produce_no_broken_links(self):
        blank = SiteSettings(
            phone="", office_phone="", whatsapp_phone="", email="", booking_email="",
            address_line="", map_query="",
        )
        for href in [
            blank.phone_href, blank.office_phone_href, blank.whatsapp_href,
            blank.email_href, blank.booking_email_href, blank.maps_href,
        ]:
            self.assertEqual(href, "")

    def test_contact_page_renders_every_actionable_link(self):
        html = self.client.get("/az/elaqe/").content.decode()
        self.assertIn('href="tel:+994515557744"', html)
        self.assertIn('href="tel:+994123103435"', html)
        self.assertIn('href="https://wa.me/994515557744"', html)
        self.assertIn('href="mailto:office@as-artgroup.az"', html)
        self.assertIn("js-map-link", html)

    def test_map_link_carries_the_query_for_the_android_upgrade(self):
        html = self.client.get("/az/elaqe/").content.decode()
        self.assertIn('data-map-query="Cəfər Cabbarlı 40, Caspian Business Center AZ1065"', html)


class SeedCommandTests(BaseTestCase):
    def test_seed_all_is_idempotent(self):
        call_command("seed_all", stdout=StringIO())
        counts = self._counts()
        call_command("seed_all", stdout=StringIO())
        self.assertEqual(counts, self._counts())

    def test_seed_all_loads_both_languages(self):
        call_command("seed_all", stdout=StringIO())
        tag = ServiceTag.objects.get(order=1)
        self.assertEqual(tag.label_az, "Tədbirlər")
        self.assertEqual(tag.label_ru, "Мероприятия")

    def _counts(self):
        return {
            "service_tags": ServiceTag.objects.count(),
            "stats": Stat.objects.count(),
            "hero_features": HeroFeature.objects.count(),
            "equipment_categories": EquipmentCategory.objects.count(),
            "equipment_tags": EquipmentTag.objects.count(),
            "project_categories": ProjectCategory.objects.count(),
            "projects": Project.objects.count(),
            "team_members": TeamMember.objects.count(),
        }


class AbsoluteURLFieldTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.field = AbsoluteURLField()
        request = RequestFactory().get("/")
        self.field._context = {"request": request}

    def test_relative_media_path_becomes_absolute(self):
        self.assertEqual(
            self.field.to_representation("/media/projects/a.jpg"),
            "http://testserver/media/projects/a.jpg",
        )

    def test_external_url_passes_through(self):
        self.assertEqual(
            self.field.to_representation("https://example.com/a.jpg"), "https://example.com/a.jpg"
        )

    def test_empty_value_returns_empty_string(self):
        self.assertEqual(self.field.to_representation(""), "")


class CoreAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        SiteSettings.load()
        ServiceTag.objects.create(label_az="Tədbirlər", label_ru="Мероприятия", order=1)

    def test_api_root_lists_endpoints(self):
        response = self.client.get("/api/v1/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("projects", response.json())
        self.assertIn("contact-messages", response.json())

    def test_site_settings_endpoint_exposes_both_languages(self):
        response = self.client.get("/api/v1/core/site-settings/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("site_tagline_az", response.json())
        self.assertIn("site_tagline_ru", response.json())

    def test_service_tags_endpoint(self):
        response = self.client.get("/api/v1/core/service-tags/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
