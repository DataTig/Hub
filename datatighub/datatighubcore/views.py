import django.contrib.auth
from django.shortcuts import render
from django.views import View

from datatighubgit.models import GitRepository
from datatighubgithub.models import GitHubRepository


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
