from django.core.management.base import BaseCommand

from datatighubgit.models import GitBranch, GitRepository
from datatighubgit.tasks import check_git_repository_and_build_if_needed


class Command(BaseCommand):
    help = "Check and build if needed"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for gh_repo in GitRepository.objects.filter(deleted=False):
            for gh_branch in GitBranch.objects.filter(repository=gh_repo, deleted=False):
                print(
                    "Git repo {}({}) @{}".format(
                        gh_repo.slug,
                        gh_repo.git_url,
                        gh_branch.branch_name,
                    )
                )
                check_git_repository_and_build_if_needed.apply_async(args=[gh_repo.id, gh_branch.id])
