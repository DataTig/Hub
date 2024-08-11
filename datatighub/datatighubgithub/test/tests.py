from django.test import TestCase

from datatighubgithub.models import GitHubRepository, GitHubRepositoryWrapper


class GitHubRepositoryModelTestCase(TestCase):
    def test_get_title(self):
        x = GitHubRepository()
        x.title = "Test"
        assert "Test" == x.get_title()

    def test_get_title_fallback(self):
        x = GitHubRepository()
        x.slug = "repo"
        x.wrapper = GitHubRepositoryWrapper()
        x.wrapper.slug = "org"
        assert "org/repo" == x.get_title()
