from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.views import View


class IndexView(
    PermissionRequiredMixin,
    View,
):

    permission_required = "datatighubcore.admin"

    def get(self, request):

        return render(
            request,
            "datatighub/github/admin/index.html",
            {},
        )
