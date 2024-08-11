from django.contrib import admin

from .models import GitHubBranch, GitHubBuild, GitHubRepository, GitHubRepositoryWrapper

admin.site.register(GitHubRepositoryWrapper)
admin.site.register(GitHubRepository)
admin.site.register(GitHubBranch)
admin.site.register(GitHubBuild)
