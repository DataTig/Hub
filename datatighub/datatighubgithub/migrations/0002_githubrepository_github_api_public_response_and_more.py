# Generated by Django 5.0.6 on 2024-06-28 08:15

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("datatighubgithub", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="githubrepository",
            name="github_api_public_response",
            field=models.JSONField(null=True),
        ),
        migrations.AddField(
            model_name="githubrepository",
            name="github_api_public_response_updated",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name="githubrepository",
            name="github_id",
            field=models.BigIntegerField(null=True, unique=True),
        ),
        migrations.AddField(
            model_name="githubrepositorywrapper",
            name="github_api_public_response",
            field=models.JSONField(null=True),
        ),
        migrations.AddField(
            model_name="githubrepositorywrapper",
            name="github_api_public_response_updated",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name="githubrepositorywrapper",
            name="github_id",
            field=models.BigIntegerField(null=True, unique=True),
        ),
        migrations.AddField(
            model_name="githubrepositorywrapper",
            name="wrapper_type",
            field=models.CharField(choices=[("ORGANISATION", "Organisation"), ("USER", "User")], null=True),
        ),
        migrations.CreateModel(
            name="GitHubRepositoryOldSlug",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("old_slug", models.CharField(max_length=500)),
                ("created", models.DateTimeField()),
                (
                    "repository",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="datatighubgithub.githubrepository",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="GitHubRepositoryWrapperOldSlug",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("old_slug", models.CharField(max_length=500)),
                ("created", models.DateTimeField()),
                (
                    "wrapper",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="datatighubgithub.githubrepositorywrapper",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="GitHubUser",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("github_id", models.BigIntegerField(unique=True)),
                ("token", models.JSONField(null=True)),
                ("github_api_user_response", models.JSONField()),
                ("github_api_user_response_updated", models.DateTimeField()),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="GitHubSubmission",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created", models.DateTimeField()),
                (
                    "type",
                    models.CharField(choices=[("EDIT", "Edit"), ("NEW", "New")], null=True),
                ),
                ("data", models.JSONField()),
                ("commit_message", models.TextField()),
                ("type_id", models.CharField()),
                ("record_id", models.CharField(null=True)),
                ("git_filename", models.CharField()),
                ("commit_sha", models.CharField()),
                ("new_branch_name", models.CharField()),
                ("finished", models.DateTimeField(null=True)),
                ("redirect_url", models.CharField(null=True)),
                ("failed", models.DateTimeField(null=True)),
                (
                    "branch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="datatighubgithub.githubbranch",
                    ),
                ),
                (
                    "repository",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="datatighubgithub.githubrepository",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="datatighubgithub.githubuser",
                    ),
                ),
            ],
        ),
    ]
