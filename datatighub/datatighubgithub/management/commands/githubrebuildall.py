from django.core.management.base import BaseCommand

from datatighubgithub.models import GitHubBranch, GitHubBuild, GitHubRepository
from datatighubgithub.tasks import github_build_task


class Command(BaseCommand):
    help = "Rebuild all sites"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for gh_repo in GitHubRepository.objects.filter(deleted=False):
            for gh_branch in GitHubBranch.objects.filter(repository=gh_repo, deleted=False):
                print(
                    "Creating build for repo {}/{} @{}".format(
                        gh_repo.wrapper.slug,
                        gh_repo.slug,
                        gh_branch.branch_name,
                    )
                )
                build = GitHubBuild()
                build.github_repository = gh_repo
                build.github_branch = gh_branch
                build.save()
                github_build_task.apply_async_on_commit(args=[build.id])
