from django.db import models

import datatighubcore.models


class GitRepository(datatighubcore.models.BaseRepository):
    slug = models.CharField(max_length=500, null=False, unique=True)
    git_url = models.CharField(max_length=500, null=False)
    primary_branch = models.ForeignKey("GitBranch", on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return "{} {} ({})".format(self.title if self.title else "", self.git_url, self.id)

    def get_title(self):
        return self.title if self.title else self.slug


class GitBranch(datatighubcore.models.BaseBranch):
    repository = models.ForeignKey(GitRepository, on_delete=models.CASCADE, null=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["repository", "branch_name"],
                name="git unique repository branch_name",
            )
        ]

    def __str__(self):
        return "{}@{} ({})".format(
            self.repository.git_url,
            self.branch_name,
            self.id,
        )


class GitBuild(datatighubcore.models.BaseBuild):
    git_repository = models.ForeignKey(GitRepository, on_delete=models.CASCADE)
    git_branch = models.ForeignKey(GitBranch, on_delete=models.CASCADE)
