import os

from celery import shared_task
from django.conf import settings

import datatighubcore.datatig.models.siteconfig
import datatighubcore.tasks

from .lib.build_task import GitBuildTask
from .lib.check_and_build_if_needed_task import CheckAndBuildIfNeededTask
from .models import GitBranch, GitBuild, GitRepository


@shared_task
def git_build_task(build_id):
    build = GitBuild.objects.get(id=build_id)
    if not build.started:
        bt = GitBuildTask(build)
        bt.build()


@shared_task
def check_git_repository_and_build_if_needed(git_repository_id, git_branch_id):
    git_repository = GitRepository.objects.get(id=git_repository_id)
    if git_repository.deleted:
        return
    git_branch = GitBranch.objects.get(id=git_branch_id, repository=git_repository)
    if git_branch.deleted:
        return
    cabifnt = CheckAndBuildIfNeededTask(git_repository, git_branch)
    cabifnt.build()


@shared_task
def check_links_in_repository_and_branch(git_repository_id, git_branch_id):
    if not settings.DATATIG_HUB_LINK_CHECKER_ENABLED:
        return
    git_repository = GitRepository.objects.get(id=git_repository_id)
    git_branch = GitBranch.objects.get(id=git_branch_id, repository=git_repository)
    builds = GitBuild.objects.filter(
        finished__isnull=False,
        git_repository=git_repository,
        git_branch=git_branch,
    ).order_by("-created")
    if not builds:
        return
    latest_build = builds[0]
    sqlite_path = os.path.join(
        settings.DATA_STORAGE_V1,
        "git",
        "repository",
        str(git_repository.id),
        "commit",
        latest_build.commit,
        "output.sqlite",
    )
    config = datatighubcore.datatig.models.siteconfig.HubSiteConfigModel("/tmp")
    config.load_from_sqlite_database(sqlite_path)
    db = datatighubcore.datatig.sqlite.HubDatatigSqlite(config, sqlite_path)
    for url in db.get_url_field_values():
        datatighubcore.tasks.link_check.apply_async(args=[url])
