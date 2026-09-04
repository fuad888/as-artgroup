from django.core.management.base import BaseCommand

from about.models import AboutContent, Stat

STATS = [
    {
        "number": 22,
        "suffix": "",
        "label_az": "Tədbirlər",
        "label_ru": "Мероприятия",
        "description_az": "İllik keçirilən irimiqyaslı konsert və mərasimlər",
        "description_ru": "Ежегодные масштабные концерты и церемонии",
        "gradient_key": "cool",
        "order": 1,
    },
    {
        "number": 10,
        "suffix": "+",
        "label_az": "Səhnə",
        "label_ru": "Сцена",
        "description_az": "Modul səhnə konstruksiyaları və podium sistemləri",
        "description_ru": "Модульные сценические конструкции и подиумные системы",
        "gradient_key": "warm",
        "order": 2,
    },
    {
        "number": 26,
        "suffix": "+",
        "label_az": "İşıq / Səs",
        "label_ru": "Свет / Звук",
        "description_az": "İşıq və səs komplektləri, tam texniki dəstək ilə",
        "description_ru": "Комплекты света и звука с полной технической поддержкой",
        "gradient_key": "hot",
        "order": 3,
    },
]


class Command(BaseCommand):
    help = "Seed about app: AboutContent + Stat (from the original index.html copy)"

    def handle(self, *args, **options):
        about = AboutContent.load()
        about.eyebrow_az = "Haqqımızda"
        about.eyebrow_ru = "О нас"
        about.heading_az = "Şəhərin enerjisini"
        about.heading_ru = "Энергию города"
        about.heading_accent_az = "səhnəyə gətiririk"
        about.heading_accent_ru = "переносим на сцену"
        about.lead_az = (
            "AS-ART Group — Bakıda konsert və korporativ tədbirlərin tam dövrlü təşkilatçısıdır. "
            "Biz sadəcə avadanlıq qurmuruq; ideyanı işığa, səsə və emosiyaya çeviririk."
        )
        about.lead_ru = (
            "AS-ART Group — организатор полного цикла концертов и корпоративных мероприятий в Баку. "
            "Мы не просто устанавливаем оборудование — мы превращаем идею в свет, звук и эмоции."
        )
        about.body_paragraph_1_az = (
            "Komandamız memarlıq miqyaslı səhnə həlləri, line-array səs sistemləri və "
            "proqramlaşdırılan işıq şouları üzərində işləyir. Hər layihə texniki rayder, "
            "3D vizuallaşdırma və tam quraşdırma qrafiki ilə başlayır — beləliklə tədbir "
            "günü heç bir sürpriz olmur."
        )
        about.body_paragraph_1_ru = (
            "Наша команда работает над сценическими решениями архитектурного масштаба, "
            "звуковыми системами line-array и программируемыми световыми шоу. Каждый проект "
            "начинается с технического райдера, 3D-визуализации и полного графика монтажа — "
            "поэтому в день мероприятия не бывает сюрпризов."
        )
        about.body_paragraph_2_az = (
            "Heydər Əliyev Sarayından açıq hava meydanlarına, korporativ konfranslardan "
            "təntənəli mərasimlərə qədər — miqyas dəyişir, standart isə eyni qalır."
        )
        about.body_paragraph_2_ru = (
            "От Центра Гейдара Алиева до открытых площадок, от корпоративных конференций "
            "до торжественных церемоний — масштаб меняется, стандарт остаётся неизменным."
        )
        about.image_url = "https://images.unsplash.com/photo-1596306499300-0b7b1689b9f6?auto=format&fit=crop&w=1200&q=80"
        about.badge_title_az = "Bakı, Azərbaycan"
        about.badge_title_ru = "Баку, Азербайджан"
        about.badge_subtitle_az = "Baza · Studiya · Anbar"
        about.badge_subtitle_ru = "База · Студия · Склад"
        about.cta_primary_label_az = "Avadanlıq parkı"
        about.cta_primary_label_ru = "Парк оборудования"
        about.cta_secondary_label_az = "Bizimlə əlaqə"
        about.cta_secondary_label_ru = "Связаться с нами"
        about.save()

        for stat in STATS:
            Stat.objects.update_or_create(
                about=about,
                order=stat["order"],
                defaults={
                    "number": stat["number"],
                    "suffix": stat["suffix"],
                    "label_az": stat["label_az"],
                    "label_ru": stat["label_ru"],
                    "description_az": stat["description_az"],
                    "description_ru": stat["description_ru"],
                    "gradient_key": stat["gradient_key"],
                },
            )

        self.stdout.write(self.style.SUCCESS("about seeded"))
