from django.core.management.base import BaseCommand

from datatighubgithub.models import GitHubBranch, GitHubBuild, GitHubRepository, GitHubRepositoryWrapper
from datatighubgithub.tasks import (
    github_build_task,
    update_repository_from_github_api_task,
    update_repository_wrapper_from_github_api_task,
)


class Command(BaseCommand):
    help = "Add a new GitHub repo"

    def add_arguments(self, parser):
        parser.add_argument("organisation_or_user_name", type=str)
        parser.add_argument("repository_name", type=str)
        parser.add_argument("branch_name", type=str)
        parser.add_argument("datatig_config_fallback_url", type=str)

    def handle(self, *args, **options):
        try:
            wrapper = GitHubRepositoryWrapper.objects.get(slug=options["organisation_or_user_name"])
        except GitHubRepositoryWrapper.DoesNotExist:
            wrapper = GitHubRepositoryWrapper()
            wrapper.slug = options["organisation_or_user_name"]
            wrapper.save()

        repo = GitHubRepository()
        repo.wrapper = wrapper
        repo.slug = options["repository_name"]
        if options["datatig_config_fallback_url"]:
            repo.datatig_config_fallback_url = options["datatig_config_fallback_url"]
        repo.save()

        branch = GitHubBranch()
        branch.repository = repo
        branch.branch_name = options["branch_name"]
        branch.save()

        repo.primary_branch = branch
        repo.save()

        build = GitHubBuild()
        build.github_repository = repo
        build.github_branch = branch
        build.save()

        update_repository_wrapper_from_github_api_task.apply_async_on_commit(args=[wrapper.id])
        update_repository_from_github_api_task.apply_async_on_commit(args=[repo.id])
        github_build_task.apply_async_on_commit(args=[build.id])
