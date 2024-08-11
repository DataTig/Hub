from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.views import View

from .models import GitRepository


class IndexView(
    PermissionRequiredMixin,
    View,
):

    permission_required = "datatighubcore.admin"

    def get(self, request):

        return render(
            request,
            "datatighub/git/admin/index.html",
            {"repositories": GitRepository.objects.all().order_by("-listing_sort_order", "title", "slug")},
        )
