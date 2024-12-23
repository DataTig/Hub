import base64

import django.contrib.auth
import prometheus_client
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

from datatighubgit.models import GitRepository
from datatighubgithub.models import GitHubRepository

from .models import Link


class IndexView(
    View,
):
    def get(self, request):

        github_repos = GitHubRepository.objects.filter(deleted=False).order_by(
            "-listing_sort_order",
            "title",
            "wrapper",
            "slug",
        )
        git_repos = GitRepository.objects.filter(deleted=False).order_by("-listing_sort_order", "title", "slug")

        # TODO mix all repos together in one list, then resort them again by listing_sort_order and title
        # Currently GitHub will always be above git,
        # and we want any of them to be anywhere regardless of what type they are

        return render(
            request,
            "datatighub/core/index.html",
            {
                "github_repos": github_repos,
                "git_repos": git_repos,
            },
        )


class NewView(
    View,
):
    def get(self, request):

        return render(
            request,
            "datatighub/core/new.html",
            {},
        )


class AccountLogoutView(
    View,
):

    def get(self, request):

        django.contrib.auth.logout(request)

        return render(
            request,
            "datatighub/core/account/logout.html",
            {},
        )


prometheus_client.Gauge("datatighub_links_count", "DataTig Hub Links Count").set_function(
    lambda: Link.objects.all().count()
)


class SysadminMonitorAppPrometheusView(
    View,
):

    def get(self, request):
        # Configured?
        if not settings.DATATIG_HUB_SYSADMIN_MONITOR_USERNAME or not settings.DATATIG_HUB_SYSADMIN_MONITOR_PASSWORD:
            return HttpResponse(status=401)

        # Check dets?
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        token_type, _, credentials = auth_header.partition(" ")

        expected = base64.b64encode(
            (
                settings.DATATIG_HUB_SYSADMIN_MONITOR_USERNAME + ":" + settings.DATATIG_HUB_SYSADMIN_MONITOR_PASSWORD
            ).encode("UTF-8")
        ).decode()

        if token_type != "Basic" or credentials != expected:
            return HttpResponse(status=401, headers={"WWW-Authenticate": 'Basic realm="Dev", charset="UTF-8"'})

        # Do work!
        return HttpResponse(prometheus_client.generate_latest(), content_type="text/plain")
