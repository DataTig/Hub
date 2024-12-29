import datetime

import prometheus_client
from django.apps import AppConfig


class DatatighubcoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "datatighubcore"

    def ready(self):
        import datatighubcore.datatig.models.field_string
        import datatighubcore.datatig.models.field_url

        datatighubcore.datatig.models.field_url.monkey_patch()
        datatighubcore.datatig.models.field_string.monkey_patch()

        from datatighubcore.models import Link

        prometheus_client.Gauge("datatighub_links_count", "DataTig Hub Links Count").set_function(
            lambda: Link.objects.all().count()
        )
        prometheus_client.Gauge(
            "datatighub_links_checked_last_24_hours_count", "DataTig Hub Links Checked in last 24 Hours Count"
        ).set_function(
            lambda: Link.objects.filter(
                last_check_at__gte=(datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(hours=24))
            ).count()
        )
