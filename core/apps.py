from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Sayt tənzimləmələri'

    def ready(self):
        from . import checks  # noqa: F401  (registers the deploy checks)
