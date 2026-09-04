from django.core.management import call_command
from django.core.management.base import BaseCommand

SEED_ORDER = ["seed_core", "seed_home", "seed_about", "seed_equipment", "seed_projects", "seed_team"]


class Command(BaseCommand):
    help = "Run all app seed commands in dependency order"

    def handle(self, *args, **options):
        for command_name in SEED_ORDER:
            self.stdout.write(f"Running {command_name}...")
            call_command(command_name, stdout=self.stdout)

        self.stdout.write(self.style.SUCCESS("All apps seeded"))
