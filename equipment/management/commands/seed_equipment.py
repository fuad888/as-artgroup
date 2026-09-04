from django.core.management.base import BaseCommand

from equipment.models import EquipmentCategory, EquipmentTag

CATEGORIES = [
    {
        "tag_number": "01",
        "tag_label_az": "Işıq",
        "tag_label_ru": "Свет",
        "title_az": "Səhnə İşıqları",
        "title_ru": "Сценическое освещение",
        "description_az": (
            "Proqramlaşdırılan moving head, beam və wash cihazları, DMX idarəetmə "
            "və atmosfer effektləri."
        ),
        "description_ru": (
            "Программируемые приборы moving head, beam и wash, управление DMX "
            "и атмосферные эффекты."
        ),
        "image_url": "https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?auto=format&fit=crop&w=1100&q=80",
        "gradient_key": "warm",
        "order": 1,
        "tags": [
            ("Moving Head", "Moving Head"),
            ("Beam / Wash", "Beam / Wash"),
            ("DMX 512", "DMX 512"),
            ("Hazer & Fog", "Hazer & Fog"),
        ],
    },
    {
        "tag_number": "02",
        "tag_label_az": "Məkan",
        "tag_label_ru": "Локация",
        "title_az": "Heydər Əliyev Equipment",
        "title_ru": "Оборудование Центра Гейдара Алиева",
        "description_az": (
            "Mərkəzin memarlıq miqyasına uyğun səhnə, LED ekran və proyeksiya "
            "həlləri — mapping daxil."
        ),
        "description_ru": (
            "Сцена, LED-экран и проекционные решения, соответствующие "
            "архитектурному масштабу центра — включая маппинг."
        ),
        "image_url": "https://images.unsplash.com/photo-1752964758338-ded530178e18?auto=format&fit=crop&w=1100&q=80",
        "gradient_key": "cool",
        "order": 2,
        "tags": [
            ("LED Wall", "LED Wall"),
            ("Projection Mapping", "Проекционный маппинг"),
            ("Modul Səhnə", "Модульная сцена"),
            ("Rigging", "Риггинг"),
        ],
    },
    {
        "tag_number": "03",
        "tag_label_az": "Səs",
        "tag_label_ru": "Звук",
        "title_az": "Soundriglar",
        "title_ru": "Звуковые системы",
        "description_az": (
            "Line-array səs sistemləri, rəqəmsal mikserlər və səhnə monitorinqi "
            "— açıq hava və zal üçün."
        ),
        "description_ru": (
            "Звуковые системы line-array, цифровые микшеры и мониторинг на сцене "
            "— для открытых площадок и залов."
        ),
        "image_url": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=1100&q=80",
        "gradient_key": "hot",
        "order": 3,
        "tags": [
            ("Line Array", "Line Array"),
            ("Subwoofer", "Сабвуфер"),
            ("Digital Mixer", "Цифровой микшер"),
            ("In-Ear Monitor", "In-Ear мониторинг"),
        ],
    },
]


class Command(BaseCommand):
    help = "Seed equipment app: EquipmentCategory + EquipmentTag (from the original index.html copy)"

    def handle(self, *args, **options):
        for cat in CATEGORIES:
            category, _ = EquipmentCategory.objects.update_or_create(
                tag_number=cat["tag_number"],
                defaults={
                    "tag_label_az": cat["tag_label_az"],
                    "tag_label_ru": cat["tag_label_ru"],
                    "title_az": cat["title_az"],
                    "title_ru": cat["title_ru"],
                    "description_az": cat["description_az"],
                    "description_ru": cat["description_ru"],
                    "image_url": cat["image_url"],
                    "gradient_key": cat["gradient_key"],
                    "order": cat["order"],
                },
            )
            for order, (label_az, label_ru) in enumerate(cat["tags"], start=1):
                EquipmentTag.objects.update_or_create(
                    category=category,
                    order=order,
                    defaults={"label_az": label_az, "label_ru": label_ru},
                )

        self.stdout.write(self.style.SUCCESS("equipment seeded"))
