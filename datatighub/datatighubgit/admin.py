from django.contrib import admin

from .models import GitBranch, GitBuild, GitRepository

admin.site.register(GitRepository)
admin.site.register(GitBranch)
admin.site.register(GitBuild)
