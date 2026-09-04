from django.core.management.base import BaseCommand

from team.models import TeamMember

MEMBERS = [
    {
        "name": "Anar Səlimov",
        "slug": "anar-selimov",
        "role_az": "Baş Prodakşn Direktoru",
        "role_ru": "Главный директор продакшна",
        "bio_az": "10+ illik təcrübə ilə irimiqyaslı tədbirlərin ucdan-uca idarə edilməsinə cavabdehdir.",
        "bio_ru": "С опытом более 10 лет отвечает за сквозное управление масштабными мероприятиями.",
        "photo_url": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=600&q=80",
        "order": 1,
    },
    {
        "name": "Leyla Hüseynova",
        "slug": "leyla-huseynova",
        "role_az": "Kreativ Direktor",
        "role_ru": "Креативный директор",
        "bio_az": "Konsepsiyadan vizual dünyaya qədər hər layihənin kreativ istiqamətini müəyyən edir.",
        "bio_ru": "Определяет творческое направление каждого проекта — от концепции до визуального мира.",
        "photo_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=600&q=80",
        "order": 2,
    },
    {
        "name": "Rəşad Quliyev",
        "slug": "resad-quliyev",
        "role_az": "Baş Səs Mühəndisi",
        "role_ru": "Главный звукоинженер",
        "bio_az": "Line-array sistemləri və zal akustikası üzrə ixtisaslaşmış mühəndis.",
        "bio_ru": "Инженер, специализирующийся на системах line-array и акустике залов.",
        "photo_url": "https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=600&q=80",
        "order": 3,
    },
    {
        "name": "Nigar Məmmədli",
        "slug": "nigar-memmedli",
        "role_az": "Tədbir Meneceri",
        "role_ru": "Менеджер мероприятий",
        "bio_az": "Planlaşdırmadan icraya qədər tədbir günü axınının koordinatoru.",
        "bio_ru": "Координатор всего процесса мероприятия — от планирования до реализации.",
        "photo_url": "https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=600&q=80",
        "order": 4,
    },
    {
        "name": "Elvin Bayramov",
        "slug": "elvin-bayramov",
        "role_az": "İşıq Dizayneri",
        "role_ru": "Дизайнер света",
        "bio_az": "Proqramlaşdırılan işıq şouları və atmosfer dizaynı üzrə çalışır.",
        "bio_ru": "Работает над программируемыми световыми шоу и атмосферным дизайном.",
        "photo_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80",
        "order": 5,
    },
    {
        "name": "Aysel Rəhimli",
        "slug": "aysel-rehimli",
        "role_az": "Səhnə Rejissoru",
        "role_ru": "Режиссёр сцены",
        "bio_az": "Tədbir günü səhnə arxası axınını və vaxt cədvəlini idarə edir.",
        "bio_ru": "Управляет закулисным процессом и тайм-кодом в день мероприятия.",
        "photo_url": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=crop&w=600&q=80",
        "order": 6,
    },
    {
        "name": "Tural Əliyev",
        "slug": "tural-eliyev",
        "role_az": "Aparıcı / Spiker",
        "role_ru": "Ведущий / Спикер",
        "bio_az": "Konsert və korporativ tədbirlərdə səhnə aparıcılığı edir.",
        "bio_ru": "Ведёт концертные и корпоративные мероприятия на сцене.",
        "photo_url": "https://images.unsplash.com/photo-1610652492500-ded49ceeb378?auto=format&fit=crop&w=600&q=80",
        "order": 7,
    },
    {
        "name": "Günel Xəlilova",
        "slug": "gunel-xelilova",
        "role_az": "Kommunikasiya Rəhbəri",
        "role_ru": "Руководитель коммуникаций",
        "bio_az": "Müştərilərlə əlaqə və layihə kommunikasiyasının aparılmasına cavabdehdir.",
        "bio_ru": "Отвечает за коммуникацию с клиентами и ведение проектной коммуникации.",
        "photo_url": "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=600&q=80",
        "order": 8,
    },
]


class Command(BaseCommand):
    help = "Seed team app: TeamMember (from the original index.html copy)"

    def handle(self, *args, **options):
        for m in MEMBERS:
            TeamMember.objects.update_or_create(
                slug=m["slug"],
                defaults={
                    "name": m["name"],
                    "role_az": m["role_az"],
                    "role_ru": m["role_ru"],
                    "bio_az": m["bio_az"],
                    "bio_ru": m["bio_ru"],
                    "photo_url": m["photo_url"],
                    "order": m["order"],
                },
            )

        self.stdout.write(self.style.SUCCESS("team seeded"))
