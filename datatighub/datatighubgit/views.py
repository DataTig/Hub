import json
import os.path
import urllib.parse

import django.urls
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

import datatighubcore.datatig.models.siteconfig
import datatighubcore.datatig.sqlite
import datatighubgit.views_base

from .models import GitBranch, GitBuild, GitRepository
from .tasks import check_git_repository_and_build_if_needed


class GitRepositoryView(View):

    def __init__(self):
        self._repository = None

    def repository_view_setup(self, request, repository_slug):
        self._repository = GitRepository.objects.get(slug=repository_slug, deleted=False)

    def get(self, request, repository_slug):

        self.repository_view_setup(request, repository_slug)

        view_variables = {
            "repository": self._repository,
        }
        view_variables.update(
            datatighubgit.views_base.get_view_variables_repository_view(
                repository=self._repository, branch_class=GitBranch
            )
        )

        return render(
            request,
            "datatighub/git/repository/index.html",
            view_variables,
        )


class GitRepositoryBuildsView(GitRepositoryView):
    def get(self, request, repository_slug):

        self.repository_view_setup(request, repository_slug)

        view_variables = {
            "repository": self._repository,
        }
        view_variables.update(
            datatighubgit.views_base.get_view_variables_repository_builds_view(
                build_search=GitBuild.objects.filter(git_repository=self._repository)
            )
        )

        return render(
            request,
            "datatighub/git/repository/builds.html",
            view_variables,
        )


@method_decorator(csrf_exempt, name="dispatch")
class GitRepositorWebhookView(
    GitRepositoryView,
):
    def post(self, request, repository_slug, webhook_code):
        return self.get(request, repository_slug, webhook_code)

    def get(self, request, repository_slug, webhook_code):

        self.repository_view_setup(request, repository_slug)

        if webhook_code != self._repository.webhook_code:
            raise PermissionDenied

        for gh_branch in GitBranch.objects.filter(repository=self._repository, deleted=False):
            check_git_repository_and_build_if_needed.apply_async(args=[self._repository.id, gh_branch.id])

        return HttpResponse("OK")


class GitRepositoryTreeView(
    GitRepositoryView,
):

    def __init__(self):
        self._branch = None
        self._latest_build = None
        self._sqlite_path = None
        self._config = None
        self._db = None

    def repository_tree_view_setup(self, request, repository_slug, tree_name):
        self.repository_view_setup(request, repository_slug)
        self._branch = GitBranch.objects.get(branch_name=tree_name, repository=self._repository, deleted=False)
        builds = GitBuild.objects.filter(
            finished__isnull=False,
            git_repository=self._repository,
            git_branch=self._branch,
        ).order_by("-created")
        if not builds:
            raise Http404("Build not found")
        self._latest_build = builds[0]
        self._sqlite_path = os.path.join(
            settings.DATA_STORAGE_V1,
            "git",
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

    def get(self, request, repository_slug, tree_name):

        self.repository_tree_view_setup(request, repository_slug, tree_name)

        db_url = request.build_absolute_uri(
            django.urls.reverse(
                "datatighubgit_repository:tree_download_sqlite_index",
                kwargs={"repository_slug": repository_slug, "tree_name": tree_name},
            )
        )

        return render(
            request,
            "datatighub/git/repository/tree/index.data.html",
            {
                "types": self.get_config().get_types().values(),
                "calendars": self.get_config().get_calendars().values(),
                "repository": self._repository,
                "branch": self._branch,
                "datasette_url": "https://lite.datasette.io/?url=" + urllib.parse.quote_plus(db_url),
            },
        )


class GitRepositoryTreeErrorsView(
    GitRepositoryTreeView,
):

    def get(self, request, repository_slug, tree_name):

        self.repository_tree_view_setup(request, repository_slug, tree_name)

        view_variables = {
            "repository": self._repository,
            "branch": self._branch,
        }
        view_variables.update(
            datatighubgit.views_base.get_view_variables_repository_tree_errors_view(sqlite_path=self._sqlite_path)
        )

        return render(
            request,
            "datatighub/git/repository/tree/errors.html",
            view_variables,
        )


class GitRepositoryTreeAPI1View(
    GitRepositoryTreeView,
):

    def get(self, request, repository_slug, tree_name):

        self.repository_tree_view_setup(request, repository_slug, tree_name)

        data = datatighubgit.views_base.get_view_variables_repository_tree_api1_view(sqlite_path=self._sqlite_path)

        return HttpResponse(json.dumps(data), content_type="application/json")


class GitRepositoryTreeDownloadSQLiteView(
    GitRepositoryTreeView,
):

    def get(self, request, repository_slug, tree_name):

        self.repository_tree_view_setup(request, repository_slug, tree_name)

        with open(self._sqlite_path, "rb") as fp:
            return HttpResponse(
                fp.read(),
                headers={
                    "Content-Type": "application/x-sqlite3",
                    "Content-Disposition": 'attachment; filename="database.sqlite"',
                    "access-control-allow-origin": "*",
                },
            )


class GitRepositoryTreeDownloadFrictionlessView(
    GitRepositoryTreeView,
):

    def get(self, request, repository_slug, tree_name):

        self.repository_tree_view_setup(request, repository_slug, tree_name)

        with open(
            os.path.join(
                settings.DATA_STORAGE_V1,
                "git",
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


class GitRepositoryTreeTypeView(
    GitRepositoryTreeView,
):

    def repository_tree_type_view_setup(self, request, repository_slug, tree_name, type_id):
        self.repository_tree_view_setup(request, repository_slug, tree_name)

        self._type = self.get_config().get_type(type_id)
        if not self._type:
            raise Http404("Type not found")

    def get(self, request, repository_slug, tree_name, type_id):

        self.repository_tree_type_view_setup(request, repository_slug, tree_name, type_id)

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
            "datatighub/git/repository/tree/type/index.html",
            view_variables,
        )


class GitRepositoryTreeTypeListRecordsView(
    GitRepositoryTreeTypeView,
):

    def get(self, request, repository_slug, tree_name, type_id):

        self.repository_tree_type_view_setup(request, repository_slug, tree_name, type_id)

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
            "datatighub/git/repository/tree/type/list_records.html",
            view_variables,
        )


class GitRepositoryTreeTypeListRecordsAPI1View(
    GitRepositoryTreeTypeView,
):

    def get(self, request, repository_slug, tree_name, type_id):

        self.repository_tree_type_view_setup(request, repository_slug, tree_name, type_id)

        data = datatighubgit.views_base.get_view_variables_repository_tree_type_list_records_api1_view(
            config=self.get_config(),
            db=self.get_database(),
            type=self._type,
            request=request,
        )

        return HttpResponse(json.dumps(data), content_type="application/json")


class GitRepositoryTreeTypeAPI1View(
    GitRepositoryTreeTypeView,
):

    def get(self, request, repository_slug, tree_name, type_id):

        self.repository_tree_type_view_setup(request, repository_slug, tree_name, type_id)

        data = datatighubgit.views_base.get_view_variables_repository_tree_type_api1_view(
            sqlite_path=self._sqlite_path, type_id=type_id
        )

        return HttpResponse(json.dumps(data), content_type="application/json")


class GitRepositoryTreeTypeNewRecordView(
    GitRepositoryTreeTypeView,
):

    def get(self, request, repository_slug, tree_name, type_id):

        self.repository_tree_type_view_setup(request, repository_slug, tree_name, type_id)

        view_variables = {
            "repository": self._repository,
            "branch": self._branch,
        }
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
            "datatighub/git/repository/tree/type/new_record.html",
            view_variables,
        )


class GitRepositoryTreeTypeRecordView(
    GitRepositoryTreeTypeView,
):

    def repository_tree_type_record_view_setup(self, request, repository_slug, tree_name, type_id, record_id):
        self.repository_tree_type_view_setup(request, repository_slug, tree_name, type_id)

        self._record = self.get_database().get_item(type_id, record_id)
        if not self._record:
            raise Http404("Record not found")

    def get(self, request, repository_slug, tree_name, type_id, record_id):

        self.repository_tree_type_record_view_setup(request, repository_slug, tree_name, type_id, record_id)

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
            "datatighub/git/repository/tree/type/record/index.html",
            view_variables,
        )


class GitRepositoryTreeTypeRecordAPI1View(
    GitRepositoryTreeTypeRecordView,
):

    def get(self, request, repository_slug, tree_name, type_id, record_id):

        self.repository_tree_type_record_view_setup(request, repository_slug, tree_name, type_id, record_id)

        data = datatighubgit.views_base.get_view_variables_repository_tree_type_record_api1_view(
            config=self.get_config(),
            db=self.get_database(),
            type=self._type,
            record=self._record,
        )

        return HttpResponse(json.dumps(data), content_type="application/json")


class GitRepositoryTreeTypeRecordEditView(
    GitRepositoryTreeTypeRecordView,
):

    def get(self, request, repository_slug, tree_name, type_id, record_id):

        self.repository_tree_type_record_view_setup(request, repository_slug, tree_name, type_id, record_id)

        view_variables = {
            "repository": self._repository,
            "branch": self._branch,
        }
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
            "datatighub/git/repository/tree/type/record/edit.html",
            view_variables,
        )


class GitRepositoryTreeTypeFieldView(
    GitRepositoryTreeTypeView,
):

    def get(self, request, repository_slug, tree_name, type_id, field_id):

        self.repository_tree_type_view_setup(request, repository_slug, tree_name, type_id)

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
            "datatighub/git/repository/tree/type/field/index.html",
            view_variables,
        )


class GitRepositoryTreeCalendarView(
    GitRepositoryTreeView,
):

    def repository_tree_view_calendar_setup(self, request, repository_slug, tree_name, calendar_id):
        self.repository_tree_view_setup(request, repository_slug, tree_name)

        self._calendar = self.get_config().get_calendar(calendar_id)
        if not self._calendar:
            raise Http404("calendar not found")

    def get(self, request, repository_slug, tree_name, calendar_id):

        self.repository_tree_view_calendar_setup(request, repository_slug, tree_name, calendar_id)

        return render(
            request,
            "datatighub/git/repository/tree/calendar/index.html",
            {
                "calendar": self._calendar,
                "repository": self._repository,
                "branch": self._branch,
            },
        )


class GitRepositoryTreeCalendarAPI1View(
    GitRepositoryTreeCalendarView,
):

    def get(self, request, repository_slug, tree_name, calendar_id):

        self.repository_tree_view_calendar_setup(request, repository_slug, tree_name, calendar_id)

        data = datatighubgit.views_base.get_view_variables_repository_tree_calendar_api1_view(
            sqlite_path=self._sqlite_path, calendar_id=calendar_id
        )

        return HttpResponse(json.dumps(data), content_type="application/json")


class GitRepositoryTreeCalendarFullCalendarDataView(
    GitRepositoryTreeCalendarView,
):

    def get(self, request, repository_slug, tree_name, calendar_id):

        self.repository_tree_view_calendar_setup(request, repository_slug, tree_name, calendar_id)

        data = datatighubgit.views_base.get_view_variables_repository_tree_calendar_fullcalendar_data_view(
            config=self.get_config(),
            db=self.get_database(),
            calendar_id=calendar_id,
            url_path_name="datatighubgit_repository:tree_type_record_index",
            url_parameters={
                "repository_slug": self._repository.slug,
                "tree_name": self._branch.branch_name,
            },
        )

        return HttpResponse(json.dumps(data), content_type="application/json")


class GitRepositoryTreeCalendarICALView(
    GitRepositoryTreeCalendarView,
):

    def get(self, request, repository_slug, tree_name, calendar_id):

        self.repository_tree_view_calendar_setup(request, repository_slug, tree_name, calendar_id)

        data = datatighubgit.views_base.get_view_variables_repository_tree_calendar_ical_view(
            config=self.get_config(),
            db=self.get_database(),
            calendar_id=calendar_id,
            repo_string_for_uid="g." + self._repository.slug + ".t." + self._branch.branch_name,
            url_path_name="datatighubgit_repository:tree_type_record_index",
            url_parameters={
                "repository_slug": self._repository.slug,
                "tree_name": self._branch.branch_name,
            },
            site_title=self._repository.get_title(),
        )

        return HttpResponse(data, content_type="text/calendar")


class GitRepositoryAdminView(
    GitRepositoryView,
):

    def is_user_allowed(self):
        # Is site admin?
        if self.request.user.has_perm("datatighubcore.admin"):
            return True

        return False

    def get(self, request, repository_slug):

        self.repository_view_setup(request, repository_slug)

        if not self.is_user_allowed():
            raise PermissionDenied()

        return render(
            request,
            "datatighub/git/repository/admin.html",
            {
                "repository": self._repository,
                "branches": GitBranch.objects.filter(repository=self._repository, deleted=False),
            },
        )
