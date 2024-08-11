from celery import shared_task
from django.conf import settings

from .lib.link_check_task import LinkCheck


@shared_task
def link_check(url):
    if not settings.DATATIG_HUB_LINK_CHECKER_ENABLED:
        return
    lc = LinkCheck(url)
    lc.process()
