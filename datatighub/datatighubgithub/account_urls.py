from django.urls import path

from . import account_views

app_name = "datatighubgithub_account"
urlpatterns = [
    path(
        "login",
        account_views.LoginView.as_view(),
        name="login",
    ),
    path(
        "callback",
        account_views.CallbackView.as_view(),
        name="callback",
    ),
]
