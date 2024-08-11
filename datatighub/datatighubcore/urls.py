from django.urls import path

from . import views

app_name = "datatighubcore"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("new", views.NewView.as_view(), name="new"),
    path(
        "account/logout",
        views.AccountLogoutView.as_view(),
        name="account_logout",
    ),
]
