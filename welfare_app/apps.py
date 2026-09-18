from django.apps import AppConfig

class WelfareAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'welfare_app'
    verbose_name = 'Welfare & Hospital Management'

    def ready(self):
        import welfare_app.signals  # noqa: F401
