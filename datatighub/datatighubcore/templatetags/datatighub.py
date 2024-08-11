from django import template
from django.conf import settings
from markdown_it import MarkdownIt

from datatighubcore.markdownitpy.setbaseurl import setbaseurl_plugin
from datatighubcore.models import Link

register = template.Library()


@register.simple_tag
def type_get_field(type, field_id):
    return type.get_field(field_id)


@register.simple_tag
def record_get_field_value(record, field_id):
    return record.get_field_value(field_id)


@register.simple_tag
def sub_record_get_value(sub_record, field_id):
    return sub_record.get_value(field_id)


@register.simple_tag
def record_filter_field_filters_for_field_id(record_filter, field_id):
    return record_filter.get_field_filters_for_field_id(field_id)


@register.simple_tag
def record_get_markdown_field_value_html(record, field_id, repository=None):
    md = MarkdownIt()
    if repository and repository.get_website_url():
        md.use(setbaseurl_plugin, base_url=repository.get_website_url())
    value = record.get_field_value(field_id).get_value()
    return md.render(value) if value else ""


@register.simple_tag
def record_url_field_get_link_check(record, field_id):
    url = record.get_field_value(field_id).get_value()
    try:
        link = Link.objects.get(url=url)
        if link and link.last_check_at:
            return link
    except Link.DoesNotExist:
        pass


@register.simple_tag
def site_domain():
    return "http{}://{}".format("s" if settings.DATATIG_HUB_HTTPS else "", settings.DATATIG_HUB_DOMAIN)
