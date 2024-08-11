from django.test import TestCase
from markdown_it import MarkdownIt

from datatighubcore.markdownitpy.setbaseurl.index import _make_url, setbaseurl_plugin


class MakeURLTestCase(TestCase):

    def testAbsoluteHTTP1(self):
        assert "http://www.example.com" == _make_url("http://www.example.com", "http://www.base.com")

    def testAbsoluteHTTPS1(self):
        assert "https://www.example.com" == _make_url("https://www.example.com", "http://www.base.com")

    def testAbsoluteWhatever1(self):
        assert "http://www.example.com" == _make_url("//www.example.com", "http://www.base.com")

    def testFromRoot1(self):
        assert "http://www.base.com/cat.png" == _make_url("/cat.png", "http://www.base.com")

    def testRelative1(self):
        assert "http://www.base.com/cat.png" == _make_url("cat.png", "http://www.base.com")

    def testFromRootWithDeepBase1(self):
        assert "http://www.base.com/cat.png" == _make_url("/cat.png", "http://www.base.com/animals")

    def testRelativeWithDeepBase1(self):
        assert "http://www.base.com/animals/cat.png" == _make_url("cat.png", "http://www.base.com/animals")


class PluginTestCase(TestCase):

    def testImage1(self):
        md = MarkdownIt()
        md.use(setbaseurl_plugin, base_url="http://www.base.com")
        out = md.render("![image](/cat.png)")
        assert '<p><img src="http://www.base.com/cat.png" alt="image" /></p>' == out.strip()

    def testLink1(self):
        md = MarkdownIt()
        md.use(setbaseurl_plugin, base_url="http://www.base.com")
        out = md.render("[pretty](cat.html)")
        assert '<p><a href="http://www.base.com/cat.html">pretty</a></p>' == out.strip()
