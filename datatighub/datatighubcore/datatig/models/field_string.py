import re

import datatig.models.field_string

from datatighubcore.models import Link


def _value_get_urls_in_value(self) -> list:
    if self._value:
        # Sometimes we have HTML here, that causes problems cos we get URLs like
        # http://cat.com">cat</a>.
        # so until we sort that look for whitespace (or start of string) in front of match to filter out any
        return [i[1] for i in re.findall(r"(\s|^)(https?://[^\s]+)", self._value)]
    else:
        return []


def _value_get_api_value(self):
    out = {"value": self._value, "urls": []}
    for url in self.get_urls_in_value():
        url_data = {"url": url, "last_check_result": None, "last_check_at": None}
        try:
            link = Link.objects.get(url=url)
            if link.last_check_at:
                url_data["last_check_result"] = link.last_check_result
                url_data["last_check_at"] = link.last_check_at.strftime("%Y-%m-%d")
        except Link.DoesNotExist:
            pass
        out["urls"].append(url_data)
    return out


def monkey_patch():
    datatig.models.field_string.FieldStringValueModel.get_urls_in_value = _value_get_urls_in_value
    datatig.models.field_string.FieldStringValueModel.get_api_value = _value_get_api_value
