from django.conf import settings
from django.core.management.base import BaseCommand

from datatighubgithub.models import GitHubBranch, GitHubRepository, GitHubRepositoryWrapper
from datatighubgithub.tasks import (
    check_github_repository_and_build_if_needed,
    check_links_in_repository_and_branch,
    update_repository_from_github_api_task,
    update_repository_wrapper_from_github_api_task,
)


class Command(BaseCommand):
    help = "Check and build if needed"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        # Update Organisations/Users Info
        for gh_repo_wrapper in GitHubRepositoryWrapper.objects.filter(deleted=False):
            update_repository_wrapper_from_github_api_task.apply_async(args=[gh_repo_wrapper.id])

        # Update Repository Info
        for gh_repo in GitHubRepository.objects.filter(deleted=False):
            update_repository_from_github_api_task.apply_async(args=[gh_repo.id])

        # Check and Build if needed
        for gh_repo in GitHubRepository.objects.filter(deleted=False):
            for gh_branch in GitHubBranch.objects.filter(repository=gh_repo, deleted=False):
                print(
                    "Check and build if needed - GitHub repo {}/{} @{}".format(
                        gh_repo.wrapper.slug,
                        gh_repo.slug,
                        gh_branch.branch_name,
                    )
                )
                check_github_repository_and_build_if_needed.apply_async(args=[gh_repo.id, gh_branch.id])

        # Check links
        if settings.DATATIG_HUB_LINK_CHECKER_ENABLED:
            for gh_repo in GitHubRepository.objects.filter(deleted=False):
                for gh_branch in GitHubBranch.objects.filter(repository=gh_repo, deleted=False):
                    print(
                        "Check links in - GitHub repo {}/{} @{}".format(
                            gh_repo.wrapper.slug,
                            gh_repo.slug,
                            gh_branch.branch_name,
                        )
                    )
                    check_links_in_repository_and_branch.apply_async(args=[gh_repo.id, gh_branch.id])
