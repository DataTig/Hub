import prometheus_client
from django.apps import AppConfig


class DatatighubgithubConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "datatighubgithub"

    def ready(self):

        from datatighubgithub.models import GitHubBranch, GitHubBuild, GitHubRepository, GitHubSubmission, GitHubUser

        prometheus_client.Gauge(
            "datatighub_github_repository_count", "DataTig Hub GitHub Repository Count"
        ).set_function(lambda: GitHubRepository.objects.all().count())
        prometheus_client.Gauge("datatighub_github_branch_count", "DataTig Hub GitHub Branch Count").set_function(
            lambda: GitHubBranch.objects.all().count()
        )
        prometheus_client.Gauge("datatighub_github_build_count", "DataTig Hub GitHub Build Count").set_function(
            lambda: GitHubBuild.objects.all().count()
        )
        prometheus_client.Gauge("datatighub_github_user_count", "DataTig Hub GitHub User Count").set_function(
            lambda: GitHubUser.objects.all().count()
        )
        prometheus_client.Gauge(
            "datatighub_github_submission_count", "DataTig Hub GitHub Submission Count"
        ).set_function(lambda: GitHubSubmission.objects.all().count())
