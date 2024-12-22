from django.apps import AppConfig


class DatatighubcoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "datatighubcore"

    def ready(self):
        import datatighubcore.datatig.models.field_url

        datatighubcore.datatig.models.field_url.monkey_patch()
