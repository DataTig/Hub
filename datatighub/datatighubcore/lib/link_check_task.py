import datetime
import time
import urllib.parse
import urllib.robotparser

import lru
import requests
import requests.auth
from django.conf import settings

from datatighubcore.models import Link

ROBOTS_TXT_PARSERS: lru.LRU = lru.LRU(settings.DATATIG_HUB_LINK_CHECKER_ROBOTS_TXT_CACHE_SIZE)


class LinkCheck:

    def __init__(self, url):
        self._url = url
        self._url_parsed = urllib.parse.urlparse(self._url)

    def process(self):
        global ROBOTS_TXT_PARSERS
        # HTTP(S) only
        if not self._url or self._url_parsed.scheme not in ["http", "https"]:
            return

        # Get or create link object
        try:
            link = Link.objects.get(url=self._url)
        except Link.DoesNotExist:
            link = Link()
            link.url = self._url
            link.save()

        # If check was done recently, don't do again
        if self._has_check_been_done_recently(link):
            return

        # Start with robots.txt
        if not self._is_robots_allowed():
            link.last_check_result = Link.CheckResultChoices.ROBOT_BLOCKED
            link.last_check_at = datetime.datetime.now(tz=datetime.timezone.utc)
            link.last_check_final_url = None
            link.last_check_status_code = None
            link.save()
            return

        # Link check!
        print("Getting URL: " + self._url)
        try:
            check_response = requests.get(
                self._url,
                headers={
                    "User-Agent": settings.DATATIG_HUB_LINK_CHECKER_USER_AGENT,
                    # If a link is to a giant GB download, we only want to get a tiny bit.
                    "Range": "bytes=0-1024",
                },
                timeout=60,
                allow_redirects=True,
            )
            link.last_check_status_code = check_response.status_code
            link.last_check_final_url = check_response.url if check_response.url != self._url else None
            link.last_check_at = datetime.datetime.now(tz=datetime.timezone.utc)
            if check_response.status_code in [200]:
                link.last_check_result = Link.CheckResultChoices.SUCCESS
            elif check_response.status_code in [404]:
                link.last_check_result = Link.CheckResultChoices.FAILED
            else:
                link.last_check_result = Link.CheckResultChoices.UNCLEAR
            link.save()
        except requests.exceptions.RequestException as err:
            print("ERROR: " + str(err))
            link.last_check_status_code = None
            link.last_check_final_url = None
            link.last_check_at = datetime.datetime.now(tz=datetime.timezone.utc)
            link.last_check_result = Link.CheckResultChoices.FAILED
            link.save()

    def _has_check_been_done_recently(self, link):
        # Has ever been done?
        if not link.last_check_at:
            return False
        # Was done recently?
        delta = datetime.datetime.now(tz=datetime.timezone.utc) - link.last_check_at
        return delta.total_seconds() < settings.DATATIG_HUB_LINK_CHECKER_SECONDS_TILL_CHECK_URL_AGAIN

    def _is_robots_allowed(self):
        global ROBOTS_TXT_PARSERS
        robots_url = self._url_parsed.scheme + "://" + self._url_parsed.netloc + "/robots.txt"

        # check entry in ROBOTS_TXT_PARSERS is not too old
        if (
            ROBOTS_TXT_PARSERS.get(robots_url)
            and ROBOTS_TXT_PARSERS.get(robots_url) != "NO_ROBOTS_TXT_FOUND"
            and time.time() - ROBOTS_TXT_PARSERS.get(robots_url).mtime()
            > settings.DATATIG_HUB_LINK_CHECKER_SECONDS_TILL_CHECK_ROBOTS_TXT_AGAIN
        ):
            del ROBOTS_TXT_PARSERS[robots_url]

        # if no entry in ROBOTS_TXT_PARSERS, get one
        if not ROBOTS_TXT_PARSERS.get(robots_url):

            print("Getting Robot Rules: " + robots_url)
            try:
                robots_response = requests.get(
                    robots_url,
                    headers={
                        "User-Agent": settings.DATATIG_HUB_LINK_CHECKER_USER_AGENT,
                    },
                    timeout=60,
                )
                if robots_response.status_code in [200]:
                    ROBOTS_TXT_PARSERS[robots_url] = urllib.robotparser.RobotFileParser()
                    ROBOTS_TXT_PARSERS[robots_url].parse(robots_response.text.split("\n"))
                else:
                    ROBOTS_TXT_PARSERS[robots_url] = "NO_ROBOTS_TXT_FOUND"
            except requests.exceptions.RequestException:
                ROBOTS_TXT_PARSERS[robots_url] = "NO_ROBOTS_TXT_FOUND"

        # finally we can check
        return ROBOTS_TXT_PARSERS[robots_url] == "NO_ROBOTS_TXT_FOUND" or ROBOTS_TXT_PARSERS[robots_url].can_fetch(
            settings.DATATIG_HUB_LINK_CHECKER_USER_AGENT, self._url
        )
