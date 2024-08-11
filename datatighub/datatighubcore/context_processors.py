from django.conf import settings  # import the settings file


def datatig_hub_context_processor(request):
    return {
        "setting_datatig_hub_name": settings.DATATIG_HUB_NAME,
        "setting_datatig_hub_email": settings.DATATIG_HUB_EMAIL,
        "setting_datatig_hub_meta_robots": settings.DATATIG_HUB_META_ROBOTS,
    }
