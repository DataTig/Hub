import base64
import datetime
import json
import os
import urllib.parse

import requests
import requests.auth
from celery import shared_task
from django.conf import settings
from requests_oauthlib import OAuth2Session

import datatighubcore.datatig.models.siteconfig
import datatighubcore.tasks
from datatighubgithub.lib.check_and_build_if_needed_task import CheckAndBuildIfNeededTask

from .lib.build_task import GitHubBuildTask
from .models import (
    GitHubBranch,
    GitHubBuild,
    GitHubRepository,
    GitHubRepositoryOldSlug,
    GitHubRepositoryWrapper,
    GitHubRepositoryWrapperOldSlug,
    GitHubSubmission,
)


@shared_task
def github_build_task(build_id):
    build = GitHubBuild.objects.get(id=build_id)
    if not build.started:
        bt = GitHubBuildTask(build)
        bt.build()


@shared_task
def check_github_repository_and_build_if_needed(github_repository_id, github_branch_id):
    github_repository = GitHubRepository.objects.get(id=github_repository_id)
    if github_repository.deleted:
        return
    github_branch = GitHubBranch.objects.get(id=github_branch_id, repository=github_repository)
    if github_branch.deleted:
        return
    cabifnt = CheckAndBuildIfNeededTask(github_repository, github_branch)
    cabifnt.build()


@shared_task
def update_repository_from_github_api_task(github_repository_id):
    github_repository = GitHubRepository.objects.get(id=github_repository_id)
    if github_repository.deleted:
        return
    print(
        "update_repository_from_github_api_task for  {} {}/{} ".format(
            github_repository.id,
            github_repository.wrapper.slug,
            github_repository.slug,
        )
    )
    r = requests.get(
        (
            "https://api.github.com/repositories/{}".format(github_repository.github_id)
            if github_repository.github_id
            else "https://api.github.com/repos/{}/{}".format(github_repository.wrapper.slug, github_repository.slug)
        ),
        auth=requests.auth.HTTPBasicAuth(
            settings.DATATIG_HUB_GITHUB["OAUTH_APP_CLIENT_ID"],
            settings.DATATIG_HUB_GITHUB["OAUTH_APP_CLIENT_SECRET"],
        ),
        headers={"X-GitHub-Api-Version": "2022-11-28"},
    )
    if r.status_code == 200:
        data = r.json()
        for k in ["organization", "owner", "parent", "source"]:
            if k in data:
                del data[k]
        for k in list(data.keys()):
            if k.endswith("_url") and isinstance(data[k], str) and data[k].startswith("https://api.github.com/"):
                del data[k]
        if data["name"] != github_repository.slug:
            old_name = GitHubRepositoryOldSlug()
            old_name.repository = github_repository
            old_name.old_slug = github_repository.slug
            old_name.created = datetime.datetime.now(tz=datetime.timezone.utc)
            old_name.save()
            github_repository.slug = data["name"]
        github_repository.github_id = data["id"]
        github_repository.github_api_public_response = data
        github_repository.github_api_public_response_updated = datetime.datetime.now(tz=datetime.timezone.utc)
        github_repository.save()
    else:
        print("Status Code {} Response {}".format(r.status_code, r.text))


@shared_task
def update_repository_wrapper_from_github_api_task(github_repository_wrapper_id):
    github_repository_wrapper = GitHubRepositoryWrapper.objects.get(id=github_repository_wrapper_id)
    if github_repository_wrapper.deleted:
        return
    print(
        "update_repository_wrapper_from_github_api_task for  {} {} ".format(
            github_repository_wrapper.id, github_repository_wrapper.slug
        )
    )
    r_org = requests.get(
        (
            "https://api.github.com/organizations/{}".format(github_repository_wrapper.github_id)
            if github_repository_wrapper.github_id
            else "https://api.github.com/orgs/{}".format(github_repository_wrapper.slug)
        ),
        auth=requests.auth.HTTPBasicAuth(
            settings.DATATIG_HUB_GITHUB["OAUTH_APP_CLIENT_ID"],
            settings.DATATIG_HUB_GITHUB["OAUTH_APP_CLIENT_SECRET"],
        ),
        headers={"X-GitHub-Api-Version": "2022-11-28"},
    )
    if r_org.status_code == 200:
        data = r_org.json()
        for k in list(data.keys()):
            if k.endswith("_url") and isinstance(data[k], str) and data[k].startswith("https://api.github.com/"):
                del data[k]
        if data["login"] != github_repository_wrapper.slug:
            old_name = GitHubRepositoryWrapperOldSlug()
            old_name.wrapper = github_repository_wrapper
            old_name.old_slug = github_repository_wrapper.slug
            old_name.created = datetime.datetime.now(tz=datetime.timezone.utc)
            old_name.save()
            github_repository_wrapper.slug = data["login"]
        github_repository_wrapper.github_id = data["id"]
        github_repository_wrapper.wrapper_type = GitHubRepositoryWrapper.WrapperTypeChoices.ORGANISATION
        github_repository_wrapper.github_api_public_response = data
        github_repository_wrapper.github_api_public_response_updated = datetime.datetime.now(tz=datetime.timezone.utc)
        github_repository_wrapper.save()
    elif r_org.status_code == 404:
        r_user = requests.get(
            (
                "https://api.github.com/user/{}".format(github_repository_wrapper.github_id)
                if github_repository_wrapper.github_id
                else "https://api.github.com/users/{}".format(github_repository_wrapper.slug)
            ),
            auth=requests.auth.HTTPBasicAuth(
                settings.DATATIG_HUB_GITHUB["OAUTH_APP_CLIENT_ID"],
                settings.DATATIG_HUB_GITHUB["OAUTH_APP_CLIENT_SECRET"],
            ),
            headers={"X-GitHub-Api-Version": "2022-11-28"},
        )
        if r_user.status_code == 200:
            data = r_user.json()
            for k in list(data.keys()):
                if k.endswith("_url") and isinstance(data[k], str) and data[k].startswith("https://api.github.com/"):
                    del data[k]
            if data["login"] != github_repository_wrapper.slug:
                old_name = GitHubRepositoryWrapperOldSlug()
                old_name.wrapper = github_repository_wrapper
                old_name.old_slug = github_repository_wrapper.slug
                old_name.created = datetime.datetime.now(tz=datetime.timezone.utc)
                old_name.save()
                github_repository_wrapper.slug = data["login"]
            github_repository_wrapper.github_id = data["id"]
            github_repository_wrapper.wrapper_type = GitHubRepositoryWrapper.WrapperTypeChoices.USER
            github_repository_wrapper.github_api_public_response = data
            github_repository_wrapper.github_api_public_response_updated = datetime.datetime.now(
                tz=datetime.timezone.utc
            )
            github_repository_wrapper.save()
        else:
            print("Calling Users - Status Code {} Response {}".format(r_user.status_code, r_user.text))
    else:
        print("Calling Orgs - Status Code {} Response {}".format(r_org.status_code, r_org.text))


@shared_task
def process_github_submission_task(github_submission_id):
    github_submission = GitHubSubmission.objects.get(id=github_submission_id)
    try:
        oauth2session = OAuth2Session(
            settings.DATATIG_HUB_GITHUB["OAUTH_APP_CLIENT_ID"],
            token=github_submission.user.token,
        )

        # ---- Make Branch
        new_branch_url = "https://api.github.com/repos/{owner}/{repo}/git/refs".format(
            owner=github_submission.repository.wrapper.slug,
            repo=github_submission.repository.slug,
        )
        response = oauth2session.post(
            new_branch_url,
            data=json.dumps(
                {
                    "ref": "refs/heads/" + github_submission.new_branch_name,
                    "sha": github_submission.commit_sha,
                }
            ),
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

        if response.status_code != 201:
            github_submission.failed = datetime.datetime.now(tz=datetime.timezone.utc)
            github_submission.save()
            print("ERROR MAKING BRANCH {}".format(response.status_code))
            print(response.text)
            return

        # ---- Content
        api_url = "https://api.github.com/repos/{owner}/{repo}/contents/{path}".format(
            owner=github_submission.repository.wrapper.slug,
            repo=github_submission.repository.slug,
            path=github_submission.git_filename,
        )
        post_data = {
            "message": github_submission.commit_message,
            "branch": github_submission.new_branch_name,
            "content": base64.b64encode(github_submission.data.encode()).decode("utf8"),
        }

        # ---------------------- Get existing SHA
        if github_submission.type == GitHubSubmission.TypeChoices.EDIT:
            response = oauth2session.get(
                api_url + "?ref=" + urllib.parse.quote_plus(github_submission.new_branch_name),
                headers={
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code != 200:
                github_submission.failed = datetime.datetime.now(tz=datetime.timezone.utc)
                github_submission.save()
                print("ERROR GETTING CURRENT SHA {}".format(response.status_code))
                print(response.text)
                return

            response_json = response.json()
            post_data["sha"] = response_json["sha"]

        # ---------------------- Submit Content
        response = oauth2session.put(
            api_url,
            data=json.dumps(post_data),
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

        if response.status_code == 200 or response.status_code == 201:
            github_submission.finished = datetime.datetime.now(tz=datetime.timezone.utc)
            github_submission.redirect_url = "https://github.com/{}/{}/compare/{}...{}".format(
                github_submission.repository.wrapper.slug,
                github_submission.repository.slug,
                github_submission.branch.branch_name,
                github_submission.new_branch_name,
            )
            github_submission.save()
        else:
            github_submission.failed = datetime.datetime.now(tz=datetime.timezone.utc)
            github_submission.save()
            print("ERROR SENDING DATA {}".format(response.status_code))
            print(response.text)

    except Exception as e:
        github_submission.failed = datetime.datetime.now(tz=datetime.timezone.utc)
        github_submission.save()
        print("PYTHON ERROR {}".format(e))
        raise e


@shared_task
def check_links_in_repository_and_branch(github_repository_id, github_branch_id):
    if not settings.DATATIG_HUB_LINK_CHECKER_ENABLED:
        return
    github_repository = GitHubRepository.objects.get(id=github_repository_id)
    github_branch = GitHubBranch.objects.get(id=github_branch_id, repository=github_repository)
    builds = GitHubBuild.objects.filter(
        finished__isnull=False,
        github_repository=github_repository,
        github_branch=github_branch,
    ).order_by("-created")
    if not builds:
        return
    latest_build = builds[0]
    sqlite_path = os.path.join(
        settings.DATA_STORAGE_V1,
        "github",
        "repository",
        str(github_repository.id),
        "commit",
        latest_build.commit,
        "output.sqlite",
    )
    config = datatighubcore.datatig.models.siteconfig.HubSiteConfigModel("/tmp")
    config.load_from_sqlite_database(sqlite_path)
    db = datatighubcore.datatig.sqlite.HubDatatigSqlite(config, sqlite_path)
    for url in db.get_url_field_values():
        datatighubcore.tasks.link_check.apply_async(args=[url])
