from django.core.management.base import BaseCommand

from datatighubgit.models import GitBranch, GitBuild, GitRepository
from datatighubgit.tasks import git_build_task


class Command(BaseCommand):
    help = "Rebuild all sites"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for gh_repo in GitRepository.objects.filter(deleted=False):
            for gh_branch in GitBranch.objects.filter(repository=gh_repo, deleted=False):
                print(
                    "Creating build for repo {}({}) @{}".format(
                        gh_repo.slug,
                        gh_repo.git_url,
                        gh_branch.branch_name,
                    )
                )
                build = GitBuild()
                build.git_repository = gh_repo
                build.git_branch = gh_branch
                build.save()
                git_build_task.apply_async_on_commit(args=[build.id])
