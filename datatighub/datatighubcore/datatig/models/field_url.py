import datatig.models.field_url

from datatighubcore.models import Link


def _value_get_api_value(self):
    out = {"value": self._value, "last_check_result": None, "last_check_at": None}
    if self._value:
        try:
            link = Link.objects.get(url=self._value)
            if link.last_check_at:
                out["last_check_result"] = link.last_check_result
                out["last_check_at"] = link.last_check_at.strftime("%Y-%m-%d")
        except Link.DoesNotExist:
            pass
    return out


def monkey_patch():
    datatig.models.field_url.FieldURLValueModel.get_api_value = _value_get_api_value
