import os

from django.conf import settings

from datatighubcore.lib.check_and_build_if_needed_task import BaseCheckAndBuildIfNeededTask
from datatighubgithub.models import GitHubBuild


class CheckAndBuildIfNeededTask(BaseCheckAndBuildIfNeededTask):

    def __init__(self, github_repository, github_branch):
        self._github_repository = github_repository
        self._github_branch = github_branch

    def get_logging_message(self):
        return "CheckAndBuildIfNeededTask for repo {}/{} @{}".format(
            self._github_repository.wrapper.slug,
            self._github_repository.slug,
            self._github_branch.branch_name,
        )

    def get_new_build(self):
        build = GitHubBuild()
        build.github_repository = self._github_repository
        build.github_branch = self._github_branch
        return build

    def get_git_url(self):
        return (
            "https://github.com/" + self._github_repository.wrapper.slug + "/" + self._github_repository.slug + ".git"
        )

    def get_git_branch(self):
        return self._github_branch.branch_name

    def get_builds(self):
        return GitHubBuild.objects.filter(
            finished__isnull=False,
            github_repository=self._github_repository,
            github_branch=self._github_branch,
        ).order_by("-created")

    def get_datatig_config_fallback_url(self):
        return self._github_repository.datatig_config_fallback_url

    def get_save_dir(self):
        return os.path.join(
            settings.DATA_STORAGE_V1,
            "github",
            "repository",
            str(self._github_repository.id),
        )
