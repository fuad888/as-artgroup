from django.core.management.base import BaseCommand

from core.models import SeoSettings, ServiceTag, SiteSettings

SERVICE_TAGS = [
    {"label_az": "Tədbirlər", "label_ru": "Мероприятия", "order": 1},
    {"label_az": "Konfranslar", "label_ru": "Конференции", "order": 2},
    {"label_az": "Sərgilər", "label_ru": "Выставки", "order": 3},
    {"label_az": "Görüşlər", "label_ru": "Встречи", "order": 4},
    {"label_az": "Təntənəli Mərasimlər", "label_ru": "Торжественные церемонии", "order": 5},
]


class Command(BaseCommand):
    help = "Seed core app: SiteSettings + ServiceTag (from the original index.html copy)"

    def handle(self, *args, **options):
        settings_obj = SiteSettings.load()
        settings_obj.site_name = "AS-ART Group"
        settings_obj.site_tagline_az = "İlham Verən Təcrübələr Yaradırıq"
        settings_obj.site_tagline_ru = "Мы создаём вдохновляющие впечатления"
        settings_obj.logo_mark_text = "AS"
        settings_obj.meta_description_az = (
            "AS-ART Group — Bakıda konsert, konfrans, sərgi və təntənəli mərasimlərin "
            "tam dövrlü təşkilatı. Səhnə, işıq, səs və prodakşn."
        )
        settings_obj.meta_description_ru = (
            "AS-ART Group — организация полного цикла концертов, конференций, выставок "
            "и торжественных церемоний в Баку. Сцена, свет, звук и продакшн."
        )
        settings_obj.phone = "+994 51 555 77 44"
        settings_obj.office_phone = "+994 12 310 34 35"
        settings_obj.whatsapp_phone = "+994 51 555 77 44"
        settings_obj.email = "office@as-artgroup.az"
        settings_obj.booking_email = "booking@as-artgroup.az"
        settings_obj.address_line_az = "Cəfər Cabbarlı 40, Caspian Business Center AZ1065"
        settings_obj.address_line_ru = "Джафар Джаббарлы 40, Caspian Business Center AZ1065"
        settings_obj.map_query = "Caspian Business Center, Cəfər Cabbarlı 40, Baku AZ1065"
        settings_obj.address_note_az = "Azərbaycan · Səbail rayonu"
        settings_obj.address_note_ru = "Азербайджан · Сабаильский район"
        settings_obj.working_hours_line_az = "B.e — Cümə · 09:00 – 19:00"
        settings_obj.working_hours_line_ru = "Пн — Пт · 09:00 – 19:00"
        settings_obj.working_hours_note_az = "Tədbir günləri 24/7 dəstək"
        settings_obj.working_hours_note_ru = "В дни мероприятий поддержка 24/7"
        settings_obj.map_embed_url = (
            "https://maps.google.com/maps?q=Caspian%20Business%20Center%2C%20Cafar%20Jabbarly%2040"
            "%2C%20Baku&t=&z=16&ie=UTF8&iwloc=&output=embed"
        )
        settings_obj.footer_note_az = "Səhnə söndü, işıqlar qaldı. Növbəti layihəni bizimlə başlayın."
        settings_obj.footer_note_ru = "Сцена погасла, но свет остался. Начнём следующий проект вместе."
        settings_obj.copyright_text_az = "AS-ART Group. Bütün hüquqlar qorunur."
        settings_obj.copyright_text_ru = "AS-ART Group. Все права защищены."
        settings_obj.instagram_url = "https://instagram.com"
        settings_obj.facebook_url = "https://facebook.com"
        settings_obj.linkedin_url = "https://linkedin.com"
        settings_obj.youtube_url = "https://youtube.com"
        settings_obj.save()

        for tag in SERVICE_TAGS:
            ServiceTag.objects.update_or_create(
                order=tag["order"],
                defaults={"label_az": tag["label_az"], "label_ru": tag["label_ru"]},
            )

        # Created with indexing off on purpose — an admin turns it on at launch.
        seo = SeoSettings.load()
        if not seo.title_suffix:
            seo.title_suffix = "AS-ART Group"
            seo.save()

        self.stdout.write(self.style.SUCCESS("core seeded"))
