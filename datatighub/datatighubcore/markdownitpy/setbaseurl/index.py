import urllib.parse
from typing import Callable

from markdown_it import MarkdownIt
from markdown_it.rules_core import StateCore


def setbaseurl_plugin(
    md: MarkdownIt,
    base_url: str,
) -> None:
    md.core.ruler.push(
        "setbaseurl",
        _make_setbaseurl_func(
            base_url,
        ),
    )


def _make_setbaseurl_func(base_url: str) -> Callable[[StateCore], None]:
    def _setbaseurl_func(state: StateCore) -> None:
        for idx, token in enumerate(state.tokens):
            if token.type != "inline":
                continue
            for child_token in token.children:  # type: ignore
                if child_token.type == "image":
                    if child_token.attrs.get("src"):
                        child_token.attrs["src"] = _make_url(child_token.attrs["src"], base_url)  # type: ignore
                elif child_token.type == "link_open":
                    if child_token.attrs.get("href"):
                        child_token.attrs["href"] = _make_url(child_token.attrs["href"], base_url)  # type: ignore

    return _setbaseurl_func


def _make_url(url: str, base_url: str) -> str:
    url_bits = urllib.parse.urlparse(url)
    base_url_bits = urllib.parse.urlparse(base_url)

    # If it's just an absolute link ...
    if url_bits.scheme.lower() in ["http", "https"]:
        return url

    if url.startswith("//"):
        return base_url_bits.scheme + ":" + url

    # If it's relative to root of current site ...
    if url.startswith("/"):
        return base_url_bits.scheme + "://" + base_url_bits.netloc + url

    # If it's relative to current base ...
    if not base_url.endswith("/") and not url.startswith("/"):
        base_url += "/"

    return base_url + url
