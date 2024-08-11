import lru
import responses
from django.test import TestCase, override_settings

import datatighubcore.lib.link_check_task
from datatighubcore.models import Link
from datatighubcore.tasks import link_check


@override_settings(DATATIG_HUB_LINK_CHECKER_ENABLED=True)
class LinkCheckTestCase(TestCase):

    def setUp(self):
        datatighubcore.lib.link_check_task.ROBOTS_TXT_PARSERS = lru.LRU(100)

    def test_success_with_robots_txt(self):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, "http://test.datatig.com/robots.txt", body="", status=200)
            rsps.add(responses.GET, "http://test.datatig.com/info.html", body="", status=200)

            link_check.apply_async(args=["http://test.datatig.com/info.html"])

            links = Link.objects.all()
            assert len(links) == 1
            assert links[0].url == "http://test.datatig.com/info.html"
            assert links[0].last_check_result == Link.CheckResultChoices.SUCCESS
            assert links[0].last_check_status_code == 200
            assert links[0].last_check_final_url is None

    def test_success_without_robots_txt(self):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, "http://test.datatig.com/robots.txt", status=404)
            rsps.add(responses.GET, "http://test.datatig.com/info.html", body="", status=200)

            link_check.apply_async(args=["http://test.datatig.com/info.html"])

            links = Link.objects.all()
            assert len(links) == 1
            assert links[0].url == "http://test.datatig.com/info.html"
            assert links[0].last_check_result == Link.CheckResultChoices.SUCCESS
            assert links[0].last_check_status_code == 200
            assert links[0].last_check_final_url is None

    def test_success_with_redirect(self):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, "http://test.datatig.com/robots.txt", body="", status=200)
            rsps.add(
                responses.GET,
                "http://test.datatig.com/informationz.html",
                body="",
                status=301,
                headers={"Location": "http://test.datatig.com/info.html"},
            )
            rsps.add(responses.GET, "http://test.datatig.com/info.html", body="", status=200)

            link_check.apply_async(args=["http://test.datatig.com/informationz.html"])

            links = Link.objects.all()
            assert len(links) == 1
            assert links[0].url == "http://test.datatig.com/informationz.html"
            assert links[0].last_check_result == Link.CheckResultChoices.SUCCESS
            assert links[0].last_check_status_code == 200
            assert links[0].last_check_final_url == "http://test.datatig.com/info.html"

    def test_block_all_robots(self):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, "http://test.datatig.com/robots.txt", body="User-agent: *\nDisallow: /", status=200)

            link_check.apply_async(args=["http://test.datatig.com/info.html"])

            links = Link.objects.all()
            assert len(links) == 1
            assert links[0].url == "http://test.datatig.com/info.html"
            assert links[0].last_check_result == Link.CheckResultChoices.ROBOT_BLOCKED

    @override_settings(DATATIG_HUB_LINK_CHECKER_USER_AGENT="DataTig Hub Test Runner")
    def test_block_our_robot(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET, "http://test.datatig.com/robots.txt", body="User-agent: DataTig\nDisallow: /", status=200
            )

            link_check.apply_async(args=["http://test.datatig.com/info.html"])

            links = Link.objects.all()
            assert len(links) == 1
            assert links[0].url == "http://test.datatig.com/info.html"
            assert links[0].last_check_result == Link.CheckResultChoices.ROBOT_BLOCKED

    def test_not_a_link(self):
        with responses.RequestsMock():
            link_check.apply_async(args=["info.html"])

            links = Link.objects.all()
            assert len(links) == 0

    def test_none(self):
        with responses.RequestsMock():
            link_check.apply_async(args=[None])

            links = Link.objects.all()
            assert len(links) == 0
