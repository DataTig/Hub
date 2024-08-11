import os

from django.conf import settings

from datatighubcore.lib.build_task import BaseBuildTask


class GitHubBuildTask(BaseBuildTask):

    def __init__(self, build):
        self._build = build

    def get_logging_message(self):
        return "repo {}/{} @{}".format(
            self._build.github_repository.wrapper.slug,
            self._build.github_repository.slug,
            self._build.github_branch.branch_name,
        )

    def get_git_url(self):
        return (
            "https://github.com/"
            + self._build.github_repository.wrapper.slug
            + "/"
            + self._build.github_repository.slug
            + ".git"
        )

    def get_git_branch_name(self):
        return self._build.github_branch.branch_name

    def get_datatig_config_fallback_url(self):
        return self._build.github_repository.datatig_config_fallback_url

    def get_save_dir(self):
        return os.path.join(
            settings.DATA_STORAGE_V1,
            "github",
            "repository",
            str(self._build.github_repository.id),
        )
