from django.conf import settings
from django.core.management.base import BaseCommand

from datatighubgit.models import GitBranch, GitRepository
from datatighubgit.tasks import check_git_repository_and_build_if_needed, check_links_in_repository_and_branch


class Command(BaseCommand):
    help = "Check and build if needed"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        # Check and Build if needed
        for g_repo in GitRepository.objects.filter(deleted=False):
            for g_branch in GitBranch.objects.filter(repository=g_repo, deleted=False):
                print(
                    "Check and build if needed - {}({}) @{}".format(
                        g_repo.slug,
                        g_repo.git_url,
                        g_branch.branch_name,
                    )
                )
                check_git_repository_and_build_if_needed.apply_async(args=[g_repo.id, g_branch.id])

        # Check links
        if settings.DATATIG_HUB_LINK_CHECKER_ENABLED:
            for g_repo in GitRepository.objects.filter(deleted=False):
                for g_branch in GitBranch.objects.filter(repository=g_repo, deleted=False):
                    print(
                        "Check links in - {}({}) @{}".format(
                            g_repo.slug,
                            g_repo.git_url,
                            g_branch.branch_name,
                        )
                    )
                    check_links_in_repository_and_branch.apply_async(args=[g_repo.id, g_branch.id])
