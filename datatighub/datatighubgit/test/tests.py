from django.test import TestCase

from datatighubgit.models import GitBranch, GitBuild, GitRepository
from datatighubgit.tasks import check_git_repository_and_build_if_needed


class ProcessTestCase(TestCase):

    def setUp(self):
        repo = GitRepository()
        repo.git_url = "https://github.com/DataTig/datatig.github.io.git"
        repo.save()

        branch = GitBranch()
        branch.branch_name = "main"
        branch.repository = repo
        branch.save()

        repo.primary_branch = branch

        check_git_repository_and_build_if_needed.apply_async(args=[repo.id, branch.id])

    def test_process(self):
        builds = GitBuild.objects.all()
        assert len(builds) == 1
