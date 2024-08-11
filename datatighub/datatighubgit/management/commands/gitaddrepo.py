from django.core.management.base import BaseCommand

from datatighubgit.models import GitBranch, GitBuild, GitRepository
from datatighubgit.tasks import git_build_task


class Command(BaseCommand):
    help = "Add a new Git repo"

    def add_arguments(self, parser):
        parser.add_argument("repository_slug", type=str)
        parser.add_argument("git_url", type=str)
        parser.add_argument("branch_name", type=str)
        parser.add_argument("datatig_config_fallback_url", type=str)
        pass

    def handle(self, *args, **options):
        repo = GitRepository()
        repo.slug = options["repository_slug"]
        repo.git_url = options["git_url"]
        if options["datatig_config_fallback_url"]:
            repo.datatig_config_fallback_url = options["datatig_config_fallback_url"]
        repo.save()

        branch = GitBranch()
        branch.repository = repo
        branch.branch_name = options["branch_name"]
        branch.save()

        repo.primary_branch = branch
        repo.save()

        build = GitBuild()
        build.git_repository = repo
        build.git_branch = branch
        build.save()

        git_build_task.apply_async_on_commit(args=[build.id])
