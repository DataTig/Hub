import random
import uuid

from django.db import models


class DataTigHub(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (("admin", "Admin - All admin tasks on this server"),)


class BaseRepository(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    datatig_config_fallback_url = models.URLField(max_length=500, blank=True, null=True)
    webhook_code = models.CharField(max_length=500, null=False)
    deleted = models.BooleanField(null=False, default=False)
    title = models.CharField(null=True, blank=True, max_length=500)
    description = models.TextField(null=True, blank=True)
    listing_sort_order = models.IntegerField(null=False, default=0)
    primary_branch = models.ForeignKey("BaseBranch", on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        if not self.datatig_config_fallback_url:
            self.datatig_config_fallback_url = None
        if not self.webhook_code:
            # TODO this could also include all alphanumeric charaters
            self.webhook_code = str(random.randrange(1000, 1000000000))
        super(BaseRepository, self).save(*args, **kwargs)

    def get_description(self):
        if self.description:
            return self.description
        else:
            return ""

    def get_website_url(self):
        return None

    class Meta:
        abstract = True


class BaseBranch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    # Anything that extends this will want a version of:
    # repository = models.ForeignKey(
    #    BaseRepository, on_delete=models.CASCADE, null=False
    # )
    branch_name = models.CharField(max_length=500, null=False)
    deleted = models.BooleanField(null=False, default=False)

    class Meta:
        # Anything that extends this will want a version of:
        #    constraints = [
        #        models.UniqueConstraint(
        #           fields=["repository", "branch_name"],
        #            name="base branch unique repository branch_name",
        #        )
        #    ]
        abstract = True


class BaseBuild(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    created = models.DateTimeField(auto_now_add=True, null=False)
    started = models.DateTimeField(null=True)
    finished = models.DateTimeField(null=True)
    commit = models.CharField(max_length=40, null=True)
    exception = models.TextField(null=True)
    exception_site_configuration = models.TextField(null=True)
    failed = models.DateTimeField(null=True)

    class Meta:
        abstract = True


class Link(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    url = models.CharField(null=False, unique=True)

    class CheckResultChoices(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        UNCLEAR = "UNCLEAR", "Unclear"
        ROBOT_BLOCKED = "ROBOT_BLOCKED", "Robot blocked"
        FAILED = "FAILED", "Failed"

    last_check_result = models.CharField(null=True, choices=CheckResultChoices)
    last_check_final_url = models.CharField(null=True)
    last_check_status_code = models.IntegerField(null=True)
    last_check_at = models.DateTimeField(null=True)
