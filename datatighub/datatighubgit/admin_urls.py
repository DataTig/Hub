from django.urls import path

from . import admin_views

app_name = "datatighubgit_admin"
urlpatterns = [
    path("", admin_views.IndexView.as_view(), name="index"),
]
