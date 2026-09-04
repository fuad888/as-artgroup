from django.core.management.base import BaseCommand

from home.models import HeroContent, HeroFeature

FEATURES = [
    {
        "icon_key": "light",
        "title_az": "Peşəkar səhnə işığı",
        "title_ru": "Профессиональный сценический свет",
        "description_az": "Moving head, wash, beam və LED ekran",
        "description_ru": "Moving head, wash, beam и LED-экраны",
        "order": 1,
    },
    {
        "icon_key": "sound",
        "title_az": "Line-array səs sistemləri",
        "title_ru": "Звуковые системы line-array",
        "description_az": "Açıq hava və zal akustikası üçün",
        "description_ru": "Для открытых площадок и залов",
        "order": 2,
    },
    {
        "icon_key": "spark",
        "title_az": "Tam dövrlü prodakşn",
        "title_ru": "Продакшн полного цикла",
        "description_az": "Konsepsiya · quraşdırma · idarəetmə",
        "description_ru": "Концепция · монтаж · управление",
        "order": 3,
    },
]


class Command(BaseCommand):
    help = "Seed home app: HeroContent + HeroFeature (from the original index.html copy)"

    def handle(self, *args, **options):
        hero = HeroContent.load()
        hero.eyebrow_az = "Bakı · Azərbaycan · 2011-dən bəri"
        hero.eyebrow_ru = "Баку · Азербайджан · с 2011 года"
        hero.heading_line1_az = "İLHAM VERƏN"
        hero.heading_line1_ru = "ВДОХНОВЛЯЮЩИЕ"
        hero.heading_line2_az = "TƏCRÜBƏLƏR"
        hero.heading_line2_ru = "ВПЕЧАТЛЕНИЯ"
        hero.heading_line3_az = "YARADIRIQ"
        hero.heading_line3_ru = "СОЗДАЁМ"
        hero.lead_az = (
            "Səhnə, işıq, səs və prodakşn — konsepsiyadan son alqışa qədər. "
            "AS-ART Group tədbirinizi şəhərin yaddaşında qalan bir şouya çevirir."
        )
        hero.lead_ru = (
            "Сцена, свет, звук и продакшн — от концепции до финальных аплодисментов. "
            "AS-ART Group превращает ваше мероприятие в шоу, которое останется в памяти города."
        )
        hero.cta_primary_label_az = "Layihələrimiz"
        hero.cta_primary_label_ru = "Наши проекты"
        hero.cta_secondary_label_az = "Bizi tanıyın"
        hero.cta_secondary_label_ru = "Узнать о нас"
        hero.image_url = "https://images.unsplash.com/photo-1744704001891-5396ac15bfe9?auto=format&fit=crop&w=2400&q=80"
        hero.save()

        for feature in FEATURES:
            HeroFeature.objects.update_or_create(
                hero=hero,
                icon_key=feature["icon_key"],
                defaults={
                    "title_az": feature["title_az"],
                    "title_ru": feature["title_ru"],
                    "description_az": feature["description_az"],
                    "description_ru": feature["description_ru"],
                    "order": feature["order"],
                },
            )

        self.stdout.write(self.style.SUCCESS("home seeded"))
