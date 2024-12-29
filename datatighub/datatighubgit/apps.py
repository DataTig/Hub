import prometheus_client
from django.apps import AppConfig


class DatatighubgitConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "datatighubgit"

    def ready(self):
        from datatighubgit.models import GitBranch, GitBuild, GitRepository

        prometheus_client.Gauge("datatighub_git_repository_count", "DataTig Hub Git Repository Count").set_function(
            lambda: GitRepository.objects.all().count()
        )
        prometheus_client.Gauge("datatighub_git_branch_count", "DataTig Hub Git Branch Count").set_function(
            lambda: GitBranch.objects.all().count()
        )
        prometheus_client.Gauge("datatighub_git_build_count", "DataTig Hub Git Build Count").set_function(
            lambda: GitBuild.objects.all().count()
        )
