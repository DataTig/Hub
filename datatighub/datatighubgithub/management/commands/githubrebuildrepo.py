from django.core.management.base import BaseCommand

from datatighubgithub.models import GitHubBranch, GitHubBuild, GitHubRepository, GitHubRepositoryWrapper
from datatighubgithub.tasks import github_build_task


class Command(BaseCommand):
    help = "Rebuild specific repo"

    def add_arguments(self, parser):
        parser.add_argument("organisation_or_user_name", type=str)
        parser.add_argument("repository_name", type=str)

    def handle(self, *args, **options):
        gh_wrapper = GitHubRepositoryWrapper.objects.get(slug=options["organisation_or_user_name"], deleted=False)
        gh_repo = GitHubRepository.objects.get(wrapper=gh_wrapper, slug=options["repository_name"], deleted=False)
        for gh_branch in GitHubBranch.objects.filter(repository=gh_repo, deleted=False):
            print(
                "Creating build for repo {}/{} @{}".format(
                    gh_wrapper.slug,
                    gh_repo.slug,
                    gh_branch.branch_name,
                )
            )
            build = GitHubBuild()
            build.github_repository = gh_repo
            build.github_branch = gh_branch
            build.save()
            github_build_task.apply_async_on_commit(args=[build.id])
