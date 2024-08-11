from django.core.management.base import BaseCommand

from datatighubgithub.models import GitHubBranch, GitHubRepository
from datatighubgithub.tasks import check_github_repository_and_build_if_needed


class Command(BaseCommand):
    help = "Check and build if needed"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for gh_repo in GitHubRepository.objects.filter(deleted=False):
            for gh_branch in GitHubBranch.objects.filter(repository=gh_repo, deleted=False):
                print(
                    "GitHub repo {}/{} @{}".format(
                        gh_repo.wrapper.slug,
                        gh_repo.slug,
                        gh_branch.branch_name,
                    )
                )
                check_github_repository_and_build_if_needed.apply_async(args=[gh_repo.id, gh_branch.id])
