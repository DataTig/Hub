from django.core.management.base import BaseCommand

from datatighubgithub.models import GitHubRepository, GitHubRepositoryWrapper
from datatighubgithub.tasks import (
    update_repository_from_github_api_task,
    update_repository_wrapper_from_github_api_task,
)


class Command(BaseCommand):
    help = "Add a new GitHub repo"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        # Update Organisations/Users Info
        for gh_repo_wrapper in GitHubRepositoryWrapper.objects.filter(deleted=False):
            update_repository_wrapper_from_github_api_task.apply_async(args=[gh_repo_wrapper.id])

        # Update Repository Info
        for gh_repo in GitHubRepository.objects.filter(deleted=False):
            update_repository_from_github_api_task.apply_async_on_commit(args=[gh_repo.id])
