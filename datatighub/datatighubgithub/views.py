import datetime
import json
import os.path
import urllib.parse

import django.urls
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

import datatighubcore.datatig.models.siteconfig
import datatighubcore.datatig.sqlite
import datatighubgit.views_base

from .models import (
    GitHubBranch,
    GitHubBuild,
    GitHubRepository,
    GitHubRepositoryOldSlug,
    GitHubRepositoryWrapper,
    GitHubRepositoryWrapperOldSlug,
    GitHubSubmission,
    GitHubUser,
)
from .tasks import (
    check_github_repository_and_build_if_needed,
    process_github_submission_task,
    update_repository_from_github_api_task,
    update_repository_wrapper_from_github_api_task,
)


class GithubRepositoryView(View):

    def __init__(self):
        self._wrapper: GitHubRepositoryWrapper = None
        self._repository: GitHubRepository = None

    def repository_view_setup(self, request, org_or_user_name, repo_name):
        # Repository Wrapper
        try:
            self._wrapper = GitHubRepositoryWrapper.objects.get(slug=org_or_user_name, deleted=False)
        except GitHubRepositoryWrapper.DoesNotExist:
            old = GitHubRepositoryWrapperOldSlug.objects.filter(old_slug=org_or_user_name).order_by("-created").first()
            if old and not old.wrapper.deleted:
                # TODO should redirect user to new URL
                self._wrapper = old.wrapper
            else:
                raise Http404("Can not find Organisation Or User")
        # Repository
        try:
            self._repository = GitHubRepository.objects.get(
                wrapper=self._wrapper,
                slug=repo_name,
                deleted=False,
            )
        except GitHubRepository.DoesNotExist:
            old = (
                GitHubRepositoryOldSlug.objects.filter(old_slug=repo_name, repository__wrapper=self._wrapper)
                .order_by("-created")
                .first()
            )
            if old and not old.repository.deleted:
                # TODO should redirect user to new URL
                self._repository = old.repository
            else:
                raise Http404("Can not find repository")

    def get_github_user(self, request):
        if request.user.is_authenticated:
            try:
                return GitHubUser.objects.get(user=request.user)
            except GitHubUser.DoesNotExist:
                return None

    def get(self, request, org_or_user_name, repo_name):

        self.repository_view_setup(request, org_or_user_name, repo_name)

        view_variables = {
            "repository": self._repository,
        }
        view_variables.update(
            datatighubgit.views_base.get_view_variables_repository_view(
                repository=self._repository, branch_class=GitHubBranch
            )
        )

        return render(
            request,
            "datatighub/github/repository/index.html",
            view_variables,
        )


class GithubRepositoryBuildsView(GithubRepositoryView):
    def get(self, request, org_or_user_name, repo_name):

        self.repository_view_setup(request, org_or_user_name, repo_name)

        view_variables = {
            "repository": self._repository,
        }
        view_variables.update(
            datatighubgit.views_base.get_view_variables_repository_builds_view(
                build_search=GitHubBuild.objects.filter(github_repository=self._repository)
            )
        )

        return render(
            request,
            "datatighub/github/repository/builds.html",
            view_variables,
        )


@method_decorator(csrf_exempt, name="dispatch")
class GithubRepositorWebhookView(
    GithubRepositoryView,
):

    def post(self, request, org_or_user_name, repo_name, webhook_code):
        return self.get(request, org_or_user_name, repo_name, webhook_code)

    def get(self, request, org_or_user_name, repo_name, webhook_code):

        # Setup
        self.repository_view_setup(request, org_or_user_name, repo_name)

        # Access checks
        if webhook_code != self._repository.webhook_code:
            raise PermissionDenied

        # Update GitHub info
        update_repository_wrapper_from_github_api_task.apply_async(args=[self._repository.wrapper.id])
        update_repository_from_github_api_task.apply_async(args=[self._repository.id])

        # Check branches
        for gh_branch in GitHubBranch.objects.filter(repository=self._repository, deleted=False):
            check_github_repository_and_build_if_needed.apply_async(args=[self._repository.id, gh_branch.id])

        # Return
        return HttpResponse("OK")


class GithubRepositoryTreeView(
    GithubRepositoryView,
):

    def __init__(self):
        self._branch = None
        self._latest_build = None
        self._sqlite_path = None
        self._config = None
        self._db = None

    def repository_tree_view_setup(self, request, org_or_user_name, repo_name, tree_name):
        self.repository_view_setup(request, org_or_user_name, repo_name)
        self._branch = GitHubBranch.objects.get(branch_name=tree_name, repository=self._repository, deleted=False)
        builds = GitHubBuild.objects.filter(
            finished__isnull=False,
            github_repository=self._repository,
            github_branch=self._branch,
        ).order_by("-created")
        if not builds:
            raise Http404("Build not found")
            # TODO rase specific error (from this and other apps), catch it in new middleware, write nice page for user
        self._latest_build = builds[0]
        self._sqlite_path = os.path.join(
            settings.DATA_STORAGE_V1,
            "github",
            "repository",
            str(self._repository.id),
            "commit",
            self._latest_build.commit,
            "output.sqlite",
        )

    def get_config(self):
        if not self._config:
            self._config = datatighubcore.datatig.models.siteconfig.HubSiteConfigModel("/tmp")
            self._config.load_from_sqlite_database(self._sqlite_path)
        return self._config

    def get_database(self):
        if not self._db:
            self._db = datatighubcore.datatig.sqlite.HubDatatigSqlite(self._config, self._sqlite_path)
        return self._db

    def get(self, request, org_or_user_name, repo_name, tree_name):

        self.repository_tree_view_setup(request, org_or_user_name, repo_name, tree_name)

        db_url = request.build_absolute_uri(
            django.urls.reverse(
                "datatighubgithub_repository:tree_download_sqlite_index",
                kwargs={
                    "org_or_user_name": org_or_user_name,
                    "repo_name": repo_name,
                    "tree_name": tree_name,
                },
            )
        )

        return render(
            request,
            "datatighub/github/repository/tree/index.data.html",
            {
                "types": self.get_config().get_types().values(),
                "calendars": self.get_config().get_calendars().values(),
                "repository": self._repository,
                "branch": self._branch,
                "datasette_url": "https://lite.datasette.io/?url=" + urllib.parse.quote_plus(db_url),
            },
        )


class GithubRepositoryTreeErrorsView(
    GithubRepositoryTreeView,
):

    def get(self, request, org_or_user_name, repo_name, tree_name):

        self.repository_tree_view_setup(request, org_or_user_name, repo_name, tree_name)

        view_variables = {
            "repository": self._repository,
            "branch": self._branch,
        }
        view_variables.update(
            datatighubgit.views_base.get_view_variables_repository_tree_errors_view(sqlite_path=self._sqlite_path)
        )

        return render(request, "datatighub/github/repository/tree/errors.html", view_variables)


class GithubRepositoryTreeViewAPI1(
    GithubRepositoryTreeView,
):

    def get(self, request, org_or_user_name, repo_name, tree_name):

        self.repository_tree_view_setup(request, org_or_user_name, repo_name, tree_name)

        data = datatighubgit.views_base.get_view_variables_repository_tree_api1_view(sqlite_path=self._sqlite_path)

        return HttpResponse(json.dumps(data), content_type="application/json")


class GithubRepositoryTreeDownloadSQLiteView(
    GithubRepositoryTreeView,
):

    def get(self, request, org_or_user_name, repo_name, tree_name):

        self.repository_tree_view_setup(request, org_or_user_name, repo_name, tree_name)

        with open(self._sqlite_path, "rb") as fp:
            return HttpResponse(
                fp.read(),
                headers={
                    "Content-Type": "application/x-sqlite3",
                    "Content-Disposition": 'attachment; filename="database.sqlite"',
                    "access-control-allow-origin": "*",
                },
            )


class GithubRepositoryTreeDownloadFrictionlessView(
    GithubRepositoryTreeView,
):

    def get(self, request, org_or_user_name, repo_name, tree_name):

        self.repository_tree_view_setup(request, org_or_user_name, repo_name, tree_name)

        with open(
            os.path.join(
                settings.DATA_STORAGE_V1,
                "github",
                "repository",
                str(self._repository.id),
                "commit",
                self._latest_build.commit,
                "frictionless.zip",
            ),
            "rb",
        ) as fp:
            return HttpResponse(
                fp.read(),
                headers={
                    "Content-Type": "application/x-zip",
                    "Content-Disposition": 'attachment; filename="frictionless_csvs.zip"',
                },
            )


class GithubRepositoryTreeTypeView(
    GithubRepositoryTreeView,
):

    def repository_tree_type_view_setup(self, request, org_or_user_name, repo_name, tree_name, type_id):
        self.repository_tree_view_setup(request, org_or_user_name, repo_name, tree_name)

        self._type = self.get_config().get_type(type_id)
        if not self._type:
            raise Http404("Type not found")

    def get(self, request, org_or_user_name, repo_name, tree_name, type_id):

        self.repository_tree_type_view_setup(request, org_or_user_name, repo_name, tree_name, type_id)

        view_variables = {
            "repository": self._repository,
            "branch": self._branch,
        }
        view_variables.update(
            datatighubgit.views_base.get_view_variables_repository_tree_type_view(
                config=self.get_config(),
                db=self.get_database(),
                type=self._type,
                request=request,
            )
        )

        return render(
            request,
            "datatighub/github/repository/tree/type/index.html",
            view_variables,
        )


class GithubRepositoryTreeTypeListRecordsView(
    GithubRepositoryTreeTypeView,
):

    def get(self, request, org_or_user_name, repo_name, tree_name, type_id):

        self.repository_tree_type_view_setup(request, org_or_user_name, repo_name, tree_name, type_id)

        view_variables = {
            "repository": self._repository,
            "branch": self._branch,
        }
        view_variables.update(
            datatighubgit.views_base.get_view_variables_repository_tree_type_list_records_view(
                config=self.get_config(),
                db=self.get_database(),
                type=self._type,
                request=request,
            )
        )

        return render(
            request,
            "datatighub/github/repository/tree/type/list_records.html",
            view_variables,
        )


class GithubRepositoryTreeTypeListRecordsAPI1View(
    GithubRepositoryTreeTypeView,
):

    def get(self, request, org_or_user_name, repo_name, tree_name, type_id):

        self.repository_tree_type_view_setup(request, org_or_user_name, repo_name, tree_name, type_id)

        data = datatighubgit.views_base.get_view_variables_repository_tree_type_list_records_api1_view(
            config=self.get_config(),
            db=self.get_database(),
            type=self._type,
            request=request,
        )

        return HttpResponse(json.dumps(data), content_type="application/json")


class GithubRepositoryTreeTypeAPI1View(
    GithubRepositoryTreeTypeView,
):

    def get(self, request, org_or_user_name, repo_name, tree_name, type_id):

        self.repository_tree_type_view_setup(request, org_or_user_name, repo_name, tree_name, type_id)

        data = datatighubgit.views_base.get_view_variables_repository_tree_type_api1_view(
            sqlite_path=self._sqlite_path, type_id=type_id
        )

        return HttpResponse(json.dumps(data), content_type="application/json")


class GithubRepositoryTreeTypeNewRecordView(
    GithubRepositoryTreeTypeView,
):

    def get(self, request, org_or_user_name, repo_name, tree_name, type_id):

        self.repository_tree_type_view_setup(request, org_or_user_name, repo_name, tree_name, type_id)

        view_variables = {
            "repository": self._repository,
            "branch": self._branch,
            "github_user": self.get_github_user(request),
        }
        view_variables["can_try_submission"] = (
            view_variables["github_user"].has_token_with_scopes_for_submission()
            if view_variables["github_user"]
            else False
        )
        if view_variables["github_user"]:
            view_variables["new_branch_name"] = "datatig-{}-{}".format(
                view_variables["github_user"].login(),
                datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
            )
        view_variables.update(
            datatighubgit.views_base.get_view_variables_repository_tree_type_new_record_view(
                config=self.get_config(),
                db=self.get_database(),
                type=self._type,
                request=request,
            )
        )

        return render(
            request,
            "datatighub/github/repository/tree/type/new_record.html",
            view_variables,
        )

    def post(self, request, org_or_user_name, repo_name, tree_name, type_id):

        self.repository_tree_type_view_setup(request, org_or_user_name, repo_name, tree_name, type_id)

        github_user = self.get_github_user(request)
        if not github_user:
            return HttpResponseNotFound("No GitHub User")

        if github_user.has_token_with_scopes_for_submission():

            # We'll try and post!
            submission = GitHubSubmission()
            submission.user = github_user
            submission.repository = self._repository
            submission.branch = self._branch
            submission.created = datetime.datetime.now(tz=datetime.timezone.utc)
            submission.type = GitHubSubmission.TypeChoices.NEW
            submission.data = request.POST.get("content")
            submission.new_branch_name = request.POST.get("new_branch_name")
            submission.commit_message = request.POST.get("commit_message")
            submission.commit_sha = self._latest_build.commit
            submission.git_filename = (
                self._type.get_directory() + "/" + request.POST.get("filename") + "." + self._type.get_default_format()
            )
            submission.type_id = self._type.get_id()
            submission.save()

            process_github_submission_task.apply_async_on_commit(args=[submission.id], queue="important")

            return redirect(
                "datatighubgithub_repository:tree_type_new_record_submission",
                org_or_user_name=self._repository.wrapper.slug,
                repo_name=self._repository.slug,
                tree_name=self._branch.branch_name,
                type_id=self._type.get_id(),
                submission_id=submission.id,
            )

        else:

            # Ask user to post
            return render(
                request,
                "datatighub/github/repository/tree/type/new_record.user_submits_data.html",
                {
                    "repository": self._repository,
                    "branch": self._branch,
                    "github_user": self.get_github_user(request),
                    "type": self._type,
                    "record": self._record,
                    "content": request.POST.get("content"),
                    "commit_message": request.POST.get("commit_message"),
                    "filename": request.POST.get("filename"),
                },
            )


class GithubRepositoryTreeTypeNewRecordSubmissionView(
    GithubRepositoryTreeTypeView,
):

    def get(
        self,
        request,
        org_or_user_name,
        repo_name,
        tree_name,
        type_id,
        submission_id,
    ):

        self.repository_tree_type_view_setup(request, org_or_user_name, repo_name, tree_name, type_id)

        github_user = self.get_github_user(request)
        if not github_user:
            return HttpResponseNotFound("No GitHub User")

        submission = GitHubSubmission.objects.get(
            id=submission_id,
            repository=self._repository,
            branch=self._branch,
            type_id=self._type.get_id(),
            user=github_user,
            type=GitHubSubmission.TypeChoices.NEW,
        )

        if submission.finished:
            return redirect(submission.redirect_url)
        elif submission.failed:
            return render(
                request,
                "datatighub/github/repository/tree/type/new_record.user_submits_data.html",
                {
                    "repository": self._repository,
                    "branch": self._branch,
                    "github_user": self.get_github_user(request),
                    "type": self._type,
                    "content": submission.data,
                    "commit_message": submission.commit_message,
                    "filename": request.POST.get("filename"),
                },
            )

        else:
            return render(
                request,
                "datatighub/github/repository/tree/type/new_record.submission_wait.html",
                {
                    "repository": self._repository,
                    "branch": self._branch,
                    "github_user": self.get_github_user(request),
                    "type": self._type,
                },
            )


class GithubRepositoryTreeTypeRecordView(
    GithubRepositoryTreeTypeView,
):

    def repository_tree_type_record_view_setup(
        self, request, org_or_user_name, repo_name, tree_name, type_id, record_id
    ):
        self.repository_tree_type_view_setup(request, org_or_user_name, repo_name, tree_name, type_id)

        self._record = self.get_database().get_item(type_id, record_id)
        if not self._record:
            raise Http404("Record not found")

    def get(self, request, org_or_user_name, repo_name, tree_name, type_id, record_id):

        self.repository_tree_type_record_view_setup(request, org_or_user_name, repo_name, tree_name, type_id, record_id)

        view_variables = {
            "repository": self._repository,
            "branch": self._branch,
        }
        view_variables.update(
            datatighubgit.views_base.get_view_variables_repository_tree_type_record_view(
                sqlite_path=self._sqlite_path, type_id=type_id, record_id=record_id
            )
        )

        return render(
            request,
            "datatighub/github/repository/tree/type/record/index.html",
            view_variables,
        )


class GithubRepositoryTreeTypeRecordAPI1View(
    GithubRepositoryTreeTypeRecordView,
):

    def get(self, request, org_or_user_name, repo_name, tree_name, type_id, record_id):

        self.repository_tree_type_record_view_setup(request, org_or_user_name, repo_name, tree_name, type_id, record_id)

        data = datatighubgit.views_base.get_view_variables_repository_tree_type_record_api1_view(
            config=self.get_config(),
            db=self.get_database(),
            type=self._type,
            record=self._record,
        )

        return HttpResponse(json.dumps(data), content_type="application/json")


class GithubRepositoryTreeTypeRecordEditView(
    GithubRepositoryTreeTypeRecordView,
):

    def get(self, request, org_or_user_name, repo_name, tree_name, type_id, record_id):

        self.repository_tree_type_record_view_setup(request, org_or_user_name, repo_name, tree_name, type_id, record_id)

        view_variables = {
            "repository": self._repository,
            "branch": self._branch,
            "github_user": self.get_github_user(request),
        }
        view_variables["can_try_submission"] = (
            view_variables["github_user"].has_token_with_scopes_for_submission()
            if view_variables["github_user"]
            else False
        )
        if view_variables["github_user"]:
            view_variables["new_branch_name"] = "datatig-{}-{}".format(
                view_variables["github_user"].login(),
                datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
            )
        view_variables.update(
            datatighubgit.views_base.get_view_variables_repository_tree_type_record_edit_view(
                config=self.get_config(),
                db=self.get_database(),
                type=self._type,
                record=self._record,
            )
        )

        return render(
            request,
            "datatighub/github/repository/tree/type/record/edit.html",
            view_variables,
        )

    def post(self, request, org_or_user_name, repo_name, tree_name, type_id, record_id):

        self.repository_tree_type_record_view_setup(request, org_or_user_name, repo_name, tree_name, type_id, record_id)

        github_user = self.get_github_user(request)
        if not github_user:
            return HttpResponseNotFound("No GitHub User")

        if github_user.has_token_with_scopes_for_submission():

            # We'll try and post!
            submission = GitHubSubmission()
            submission.user = github_user
            submission.repository = self._repository
            submission.branch = self._branch
            submission.created = datetime.datetime.now(tz=datetime.timezone.utc)
            submission.type = GitHubSubmission.TypeChoices.EDIT
            submission.data = request.POST.get("content")
            submission.new_branch_name = request.POST.get("new_branch_name")
            submission.commit_message = request.POST.get("commit_message")
            submission.commit_sha = self._latest_build.commit
            submission.git_filename = self._record.get_git_filename()
            submission.type_id = self._type.get_id()
            submission.record_id = self._record.get_id()
            submission.save()

            process_github_submission_task.apply_async_on_commit(args=[submission.id], queue="important")

            return redirect(
                "datatighubgithub_repository:tree_type_record_edit_submission",
                org_or_user_name=self._repository.wrapper.slug,
                repo_name=self._repository.slug,
                tree_name=self._branch.branch_name,
                type_id=self._type.get_id(),
                record_id=self._record.get_id(),
                submission_id=submission.id,
            )

        else:

            # Ask user to post
            return render(
                request,
                "datatighub/github/repository/tree/type/record/edit.user_submits_data.html",
                {
                    "repository": self._repository,
                    "branch": self._branch,
                    "github_user": self.get_github_user(request),
                    "type": self._type,
                    "record": self._record,
                    "content": request.POST.get("content"),
                    "commit_message": request.POST.get("commit_message"),
                },
            )


class GithubRepositoryTreeTypeRecordEditSubmissionView(
    GithubRepositoryTreeTypeRecordView,
):

    def get(
        self,
        request,
        org_or_user_name,
        repo_name,
        tree_name,
        type_id,
        record_id,
        submission_id,
    ):

        self.repository_tree_type_record_view_setup(request, org_or_user_name, repo_name, tree_name, type_id, record_id)

        github_user = self.get_github_user(request)
        if not github_user:
            return HttpResponseNotFound("No GitHub User")

        submission = GitHubSubmission.objects.get(
            id=submission_id,
            repository=self._repository,
            branch=self._branch,
            type_id=self._type.get_id(),
            record_id=self._record.get_id(),
            user=github_user,
            type=GitHubSubmission.TypeChoices.EDIT,
        )

        if submission.finished:
            return redirect(submission.redirect_url)
        elif submission.failed:
            return render(
                request,
                "datatighub/github/repository/tree/type/record/edit.user_submits_data.html",
                {
                    "repository": self._repository,
                    "branch": self._branch,
                    "github_user": self.get_github_user(request),
                    "type": self._type,
                    "record": self._record,
                    "content": submission.data,
                    "commit_message": submission.commit_message,
                },
            )

        else:
            return render(
                request,
                "datatighub/github/repository/tree/type/record/edit.submission_wait.html",
                {
                    "repository": self._repository,
                    "branch": self._branch,
                    "github_user": self.get_github_user(request),
                    "type": self._type,
                    "record": self._record,
                },
            )


class GithubRepositoryTreeTypeFieldView(
    GithubRepositoryTreeTypeView,
):

    def get(self, request, org_or_user_name, repo_name, tree_name, type_id, field_id):

        self.repository_tree_type_view_setup(request, org_or_user_name, repo_name, tree_name, type_id)

        field = self._type.get_field(field_id)
        if not field:
            return HttpResponseNotFound("Field not found")

        view_variables = {
            "repository": self._repository,
            "branch": self._branch,
        }

        view_variables.update(
            datatighubgit.views_base.get_view_variables_repository_tree_type_field_view(
                config=self.get_config(),
                db=self.get_database(),
                type=self._type,
                field=field,
            )
        )

        return render(
            request,
            "datatighub/github/repository/tree/type/field/index.html",
            view_variables,
        )


class GithubRepositoryTreeCalendarView(
    GithubRepositoryTreeView,
):

    def repository_tree_view_calendar_setup(self, request, org_or_user_name, repo_name, tree_name, calendar_id):
        self.repository_tree_view_setup(request, org_or_user_name, repo_name, tree_name)

        self._calendar = self.get_config().get_calendar(calendar_id)
        if not self._calendar:
            raise Http404("Calendar not found")

    def get(self, request, org_or_user_name, repo_name, tree_name, calendar_id):

        self.repository_tree_view_calendar_setup(request, org_or_user_name, repo_name, tree_name, calendar_id)

        return render(
            request,
            "datatighub/github/repository/tree/calendar/index.html",
            {
                "calendar": self._calendar,
                "repository": self._repository,
                "branch": self._branch,
            },
        )


class GithubRepositoryTreeCalendarFullCalendarDataView(
    GithubRepositoryTreeCalendarView,
):

    def get(self, request, org_or_user_name, repo_name, tree_name, calendar_id):

        self.repository_tree_view_calendar_setup(request, org_or_user_name, repo_name, tree_name, calendar_id)

        data = datatighubgit.views_base.get_view_variables_repository_tree_calendar_fullcalendar_data_view(
            config=self.get_config(),
            db=self.get_database(),
            calendar_id=calendar_id,
            url_path_name="datatighubgithub_repository:tree_type_record_index",
            url_parameters={
                "org_or_user_name": self._wrapper.slug,
                "repo_name": self._repository.slug,
                "tree_name": self._branch.branch_name,
            },
        )

        return HttpResponse(json.dumps(data), content_type="application/json")


class GithubRepositoryTreeCalendarAPI1View(
    GithubRepositoryTreeCalendarView,
):

    def get(self, request, org_or_user_name, repo_name, tree_name, calendar_id):

        self.repository_tree_view_calendar_setup(request, org_or_user_name, repo_name, tree_name, calendar_id)

        data = datatighubgit.views_base.get_view_variables_repository_tree_calendar_api1_view(
            sqlite_path=self._sqlite_path, calendar_id=calendar_id
        )

        return HttpResponse(json.dumps(data), content_type="application/json")


class GithubRepositoryTreeCalendarICALView(
    GithubRepositoryTreeCalendarView,
):

    def get(self, request, org_or_user_name, repo_name, tree_name, calendar_id):

        self.repository_tree_view_calendar_setup(request, org_or_user_name, repo_name, tree_name, calendar_id)

        data = datatighubgit.views_base.get_view_variables_repository_tree_calendar_ical_view(
            config=self.get_config(),
            db=self.get_database(),
            calendar_id=calendar_id,
            repo_string_for_uid="gh."
            + self._wrapper.slug
            + "."
            + self._repository.slug
            + ".t."
            + self._branch.branch_name,
            url_path_name="datatighubgithub_repository:tree_type_record_index",
            url_parameters={
                "org_or_user_name": self._wrapper.slug,
                "repo_name": self._repository.slug,
                "tree_name": self._branch.branch_name,
            },
            site_title=self._repository.get_title(),
        )

        return HttpResponse(data, content_type="text/calendar")


class GithubRepositoryAdminView(
    GithubRepositoryView,
):
    def is_user_allowed(self):
        # Is site admin?
        if self.request.user.has_perm("datatighubcore.admin"):
            return True

        # TODO Check if currently logged in user has admin perms on this specific repo and allow them access, if so

        return False

    def get(self, request, org_or_user_name, repo_name):

        self.repository_view_setup(request, org_or_user_name, repo_name)

        if not self.is_user_allowed():
            raise PermissionDenied()

        return render(
            request,
            "datatighub/github/repository/admin.html",
            {
                "repository": self._repository,
                "branches": GitHubBranch.objects.filter(repository=self._repository, deleted=False),
            },
        )
