import uuid

from django.contrib.auth.models import User
from django.db import models

import datatighubcore.models


class GitHubRepositoryWrapper(models.Model):
    """
    This can be an Organisation or a User account.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    slug = models.CharField(max_length=500, null=False, unique=True)

    class WrapperTypeChoices(models.TextChoices):
        ORGANISATION = "ORGANISATION", "Organisation"
        USER = "USER", "User"

    wrapper_type = models.CharField(null=True, choices=WrapperTypeChoices)
    deleted = models.BooleanField(null=False, default=False)
    github_id = models.BigIntegerField(null=True, unique=True)
    github_api_public_response = models.JSONField(null=True)
    github_api_public_response_updated = models.DateTimeField(null=True)

    def __str__(self):
        return "{} ({})".format(
            self.slug,
            self.id,
        )


class GitHubRepositoryWrapperOldSlug(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    wrapper = models.ForeignKey(GitHubRepositoryWrapper, on_delete=models.CASCADE, null=False)
    old_slug = models.CharField(max_length=500, null=False)
    created = models.DateTimeField(null=False)


class GitHubRepository(datatighubcore.models.BaseRepository):
    wrapper = models.ForeignKey(GitHubRepositoryWrapper, on_delete=models.PROTECT, null=False)
    slug = models.CharField(max_length=500, null=False)
    primary_branch = models.ForeignKey("GitHubBranch", on_delete=models.SET_NULL, null=True)
    github_id = models.BigIntegerField(null=True, unique=True)
    github_api_public_response = models.JSONField(null=True)
    github_api_public_response_updated = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["wrapper", "slug"],
                name="unique wrapper slug",
            )
        ]

    def __str__(self):
        return "{} {}/{} ({})".format(
            self.title if self.title else "",
            self.wrapper.slug,
            self.slug,
            self.id,
        )

    def get_title(self) -> str:
        if self.title:
            return self.title
        else:
            return "{}/{}".format(self.wrapper.slug, self.slug)

    def get_description(self) -> str:
        if self.description:
            return self.description
        elif self.github_api_public_response and self.github_api_public_response.get("description"):
            return self.github_api_public_response["description"]
        else:
            return ""

    def get_website_url(self):
        if self.github_api_public_response and self.github_api_public_response.get("homepage"):
            return self.github_api_public_response.get("homepage")

    def get_github_homepage(self) -> str:
        return (
            self.github_api_public_response["homepage"]
            if self.github_api_public_response and self.github_api_public_response.get("homepage")
            else ""
        )

    def get_github_stargazers_count(self):
        return (
            self.github_api_public_response["stargazers_count"]
            if self.github_api_public_response and "stargazers_count" in self.github_api_public_response
            else None
        )

    def get_github_forks_count(self):
        return (
            self.github_api_public_response["forks_count"]
            if self.github_api_public_response and "forks_count" in self.github_api_public_response
            else None
        )


class GitHubRepositoryOldSlug(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    repository = models.ForeignKey(GitHubRepository, on_delete=models.CASCADE, null=False)
    old_slug = models.CharField(max_length=500, null=False)
    created = models.DateTimeField(null=False)


class GitHubBranch(datatighubcore.models.BaseBranch):
    repository = models.ForeignKey(GitHubRepository, on_delete=models.CASCADE, null=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["repository", "branch_name"],
                name="github unique repository branch_name",
            )
        ]

    def __str__(self):
        return "{}/{}@{} ({})".format(
            self.repository.wrapper.slug,
            self.repository.slug,
            self.branch_name,
            self.id,
        )


class GitHubBuild(datatighubcore.models.BaseBuild):
    github_repository = models.ForeignKey(GitHubRepository, on_delete=models.CASCADE)
    github_branch = models.ForeignKey(GitHubBranch, on_delete=models.CASCADE)


class GitHubUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    github_id = models.BigIntegerField(null=False, unique=True)
    token = models.JSONField(null=True)
    github_api_user_response = models.JSONField(null=False)
    github_api_user_response_updated = models.DateTimeField(null=False)

    def has_token_with_scopes_for_submission(self):
        return self.token and "repo" in self.token.get("scope")

    def login(self):
        return self.github_api_user_response.get("login", "")


class GitHubSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    repository = models.ForeignKey(GitHubRepository, on_delete=models.CASCADE, null=False)
    branch = models.ForeignKey(GitHubBranch, on_delete=models.CASCADE)
    user = models.ForeignKey(GitHubUser, on_delete=models.CASCADE)
    created = models.DateTimeField(null=False)

    class TypeChoices(models.TextChoices):
        EDIT = "EDIT", "Edit"
        NEW = "NEW", "New"

    type = models.CharField(null=True, choices=TypeChoices)
    data = models.JSONField(null=False)
    commit_message = models.TextField(null=False)
    type_id = models.CharField(null=False)
    record_id = models.CharField(null=True)
    git_filename = models.CharField(null=False)
    commit_sha = models.CharField(null=False)
    new_branch_name = models.CharField(null=False)
    finished = models.DateTimeField(null=True)
    redirect_url = models.CharField(null=True)
    failed = models.DateTimeField(null=True)
