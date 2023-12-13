from django.apps import AppConfig


class ElectoralRollConfig(AppConfig):
    name = 'electoral_roll'

    def ready(self):
        import electoral_roll.signals
