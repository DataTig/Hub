import os

from django.conf import settings

from datatighubcore.lib.check_and_build_if_needed_task import BaseCheckAndBuildIfNeededTask
from datatighubgit.models import GitBuild


class CheckAndBuildIfNeededTask(BaseCheckAndBuildIfNeededTask):

    def __init__(self, git_repository, git_branch):
        self._git_repository = git_repository
        self._git_branch = git_branch

    def get_logging_message(self):
        return "repo {}({}) @{}".format(
            self._git_repository.slug,
            self._git_repository.git_url,
            self._git_branch.branch_name,
        )

    def get_new_build(self):
        build = GitBuild()
        build.git_repository = self._git_repository
        build.git_branch = self._git_branch
        return build

    def get_git_url(self):
        return self._git_repository.git_url

    def get_git_branch(self):
        return self._git_branch.branch_name

    def get_builds(self):
        return GitBuild.objects.filter(
            finished__isnull=False,
            git_repository=self._git_repository,
            git_branch=self._git_branch,
        ).order_by("-created")

    def get_datatig_config_fallback_url(self):
        return self._git_repository.datatig_config_fallback_url

    def get_save_dir(self):
        return os.path.join(
            settings.DATA_STORAGE_V1,
            "git",
            "repository",
            str(self._git_repository.id),
        )
