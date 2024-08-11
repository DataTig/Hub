import datetime

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.views import View
from requests_oauthlib import OAuth2Session

from datatighubgithub.models import GitHubUser

AUTHORIZATION_BASE_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
USER_URL = "https://api.github.com/user"


class LoginView(
    View,
):
    def get(self, request):
        if settings.DATATIG_HUB_GITHUB["OAUTH_APP_CLIENT_ID"]:
            github = OAuth2Session(settings.DATATIG_HUB_GITHUB["OAUTH_APP_CLIENT_ID"], scope=["repo"])
            authorization_url, state = github.authorization_url(AUTHORIZATION_BASE_URL)
            request.session["github_oauth_state"] = state
            return redirect(authorization_url)
        else:
            raise Exception("GH NOT CONFIGURED")


class CallbackView(
    View,
):
    def get(self, request):
        github = OAuth2Session(
            settings.DATATIG_HUB_GITHUB["OAUTH_APP_CLIENT_ID"],
            state=request.session["github_oauth_state"],
        )
        token = github.fetch_token(
            TOKEN_URL,
            client_secret=settings.DATATIG_HUB_GITHUB["OAUTH_APP_CLIENT_SECRET"],
            code=request.GET.get("code"),
        )

        github_api_user_response = github.get(USER_URL).json()

        try:
            github_user = GitHubUser.objects.get(github_id=github_api_user_response["id"])
        except GitHubUser.DoesNotExist:
            django_user = User.objects.create_user("github" + str(github_api_user_response["id"]))
            github_user = GitHubUser()
            github_user.user = django_user
            github_user.github_id = github_api_user_response["id"]

        github_user.token = token
        github_user.github_api_user_response = github_api_user_response
        github_user.github_api_user_response_updated = datetime.datetime.now(tz=datetime.timezone.utc)
        github_user.save()

        login(request, github_user.user)

        return redirect("datatighubcore:index")
