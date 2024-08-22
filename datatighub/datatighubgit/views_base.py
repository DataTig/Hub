import datetime
import hashlib

import django.urls
import icalendar
from datatig.models.type import TypeModel
from django.conf import settings
from django.http import HttpResponseNotFound

import datatighubcore.datatig.models.siteconfig
import datatighubcore.datatig.sqlite
from datatighubcore.models import BaseBranch, BaseRepository


def get_view_variables_repository_view(repository: BaseRepository, branch_class: BaseBranch) -> dict:
    return {
        "branches": branch_class.objects.filter(repository=repository, deleted=False),
    }


def get_view_variables_repository_builds_view(build_search) -> dict:
    return {"builds": build_search.order_by("-created")}


def get_view_variables_repository_tree_errors_view(sqlite_path) -> dict:

    config = datatighubcore.datatig.models.siteconfig.HubSiteConfigModel("/tmp")
    config.load_from_sqlite_database(sqlite_path)
    db = datatighubcore.datatig.sqlite.HubDatatigSqlite(config, sqlite_path)

    return {
        "count_site_errors": db.get_count_site_errors(),
        "all_errors": db.get_all_errors_generator(),
    }


def get_view_variables_repository_tree_type_view(
    config: datatighubcore.datatig.models.siteconfig.HubSiteConfigModel,
    db: datatighubcore.datatig.sqlite.HubDatatigSqlite,
    type: TypeModel,
    request,
) -> dict:

    filter = type.get_records_filter()
    filter.load_default(number_on_page=20)
    filter.process(db)

    return {
        "type": type,
        "records": filter.get_results_records(),
        "records_meta": filter.get_results_records_meta(),
        "columns": filter.get_columns(),
        "fields": type.get_fields().values(),
    }


def get_view_variables_repository_tree_type_list_records_view(
    config: datatighubcore.datatig.models.siteconfig.HubSiteConfigModel,
    db: datatighubcore.datatig.sqlite.HubDatatigSqlite,
    type: TypeModel,
    request,
) -> dict:

    filter = type.get_records_filter()
    filter.load_from_request(request)
    filter.process(db)

    return {
        "type": type,
        "filter": filter,
        "records": filter.get_results_records(),
        "records_meta": filter.get_results_records_meta(),
        "paging_links": filter.get_paging_links(),
        "columns": filter.get_columns(),
        "fields": type.get_fields().values(),
    }


def get_view_variables_repository_tree_type_list_records_api1_view(
    config: datatighubcore.datatig.models.siteconfig.HubSiteConfigModel,
    db: datatighubcore.datatig.sqlite.HubDatatigSqlite,
    type: TypeModel,
    request,
) -> dict:

    filter = type.get_records_filter()
    filter.load_from_request(request)
    filter.process(db)

    out = {
        "records": [],
        "paging": {
            "current": filter.get_page(),
            "maximum": filter.get_results_records_meta()["total_pages"],
        },
    }

    for record in filter.get_results_records():
        record_data = {"id": record.get_id(), "fields": {}}
        for field_id in filter.get_columns():
            record_data["fields"][field_id] = record.get_field_value(field_id).get_api_value()
        out["records"].append(record_data)  # type:ignore
    return out


def get_view_variables_repository_tree_type_new_record_view(
    config: datatighubcore.datatig.models.siteconfig.HubSiteConfigModel,
    db: datatighubcore.datatig.sqlite.HubDatatigSqlite,
    type: TypeModel,
    request,
) -> dict:

    return {
        "type": type,
    }


def get_view_variables_repository_tree_type_record_view(sqlite_path, type_id, record_id) -> dict:

    config = datatighubcore.datatig.models.siteconfig.HubSiteConfigModel("/tmp")
    config.load_from_sqlite_database(sqlite_path)
    db = datatighubcore.datatig.sqlite.HubDatatigSqlite(config, sqlite_path)

    type = config.get_type(type_id)
    if not type:
        return HttpResponseNotFound("Type not found")

    record = db.get_item(type_id, record_id)
    if not record:
        return HttpResponseNotFound("Record not found")

    calendar_events = db.get_calendar_events_in_record(record)

    return {
        "type": type,
        "record": record,
        "fields": type.get_fields().values(),
        "calendar_ids": list(set([i.get_calendar_id() for i in calendar_events])),
    }


def get_view_variables_repository_tree_type_record_edit_view(
    config: datatighubcore.datatig.models.siteconfig.HubSiteConfigModel,
    db: datatighubcore.datatig.sqlite.HubDatatigSqlite,
    type,
    record,
) -> dict:

    return {
        "type": type,
        "record": record,
    }


def get_view_variables_repository_tree_type_field_view(
    config: datatighubcore.datatig.models.siteconfig.HubSiteConfigModel,
    db: datatighubcore.datatig.sqlite.HubDatatigSqlite,
    type,
    field,
) -> dict:

    return {"type": type, "field": field, "stats": db.get_field_stats(type, field)}


def get_view_variables_repository_tree_api1_view(sqlite_path) -> dict:

    config = datatighubcore.datatig.models.siteconfig.HubSiteConfigModel("/tmp")
    config.load_from_sqlite_database(sqlite_path)
    # db = datatighubcore.datatig.sqlite.HubDatatigSqlite(config, sqlite_path)

    out: dict = {
        "types": {},
        "calendars": {},
    }

    for type in config.get_types().values():
        out["types"][type.get_id()] = {"id": type.get_id()}

    for calendar in config.get_calendars().values():
        out["calendars"][calendar.get_id()] = {"id": calendar.get_id()}

    return out


def get_view_variables_repository_tree_type_api1_view(sqlite_path, type_id) -> dict:

    config = datatighubcore.datatig.models.siteconfig.HubSiteConfigModel("/tmp")
    config.load_from_sqlite_database(sqlite_path)
    # db = datatighubcore.datatig.sqlite.HubDatatigSqlite(config, sqlite_path)

    type = config.get_type(type_id)

    out = {"fields": {id: {"type": field.get_type()} for id, field in type.get_fields().items()}}

    return out


def get_view_variables_repository_tree_type_record_api1_view(
    config: datatighubcore.datatig.models.siteconfig.HubSiteConfigModel,
    db: datatighubcore.datatig.sqlite.HubDatatigSqlite,
    type,
    record,
) -> dict:

    out = {
        "data": record.get_data(),
        "git_filename": record.get_git_filename(),
        "format": record.get_format(),
        "fields": {},
    }
    for field_id in type.get_fields().keys():
        out["fields"][field_id] = record.get_field_value(field_id).get_api_value()
    return out


def get_view_variables_repository_tree_calendar_api1_view(sqlite_path, calendar_id) -> dict:

    config = datatighubcore.datatig.models.siteconfig.HubSiteConfigModel("/tmp")
    config.load_from_sqlite_database(sqlite_path)
    # db = datatighubcore.datatig.sqlite.HubDatatigSqlite(config, sqlite_path)

    out: dict = {}

    return out


def get_view_variables_repository_tree_calendar_fullcalendar_data_view(
    config: datatighubcore.datatig.models.siteconfig.HubSiteConfigModel,
    db: datatighubcore.datatig.sqlite.HubDatatigSqlite,
    calendar_id,
    url_path_name: str,
    url_parameters: dict,
):

    # TODO use filters passed to us to only get some events
    out = []
    for cal_event in db.get_calendar_events_in_calendar(calendar_id):
        url_parameters["type_id"] = cal_event._type_id
        url_parameters["record_id"] = cal_event._record_id
        out.append(
            {
                "id": cal_event.get_id(),
                "title": cal_event.get_summary(),
                "start": cal_event.get_start_iso(),
                "end": cal_event.get_end_iso(),
                "url": django.urls.reverse(url_path_name, kwargs=url_parameters),
            }
        )

    return out


def get_view_variables_repository_tree_calendar_ical_view(
    config: datatighubcore.datatig.models.siteconfig.HubSiteConfigModel,
    db: datatighubcore.datatig.sqlite.HubDatatigSqlite,
    calendar_id,
    repo_string_for_uid: str,
    url_path_name: str,
    url_parameters: dict,
    site_title: str,
):

    calendar = icalendar.Calendar()
    calendar.add(
        "X-WR-CALNAME",
        "{} {} (via {} on {})".format(calendar_id, config.get_title(), site_title, settings.DATATIG_HUB_NAME),
    )
    for cal_event in db.get_calendar_events_in_calendar(calendar_id):
        url_parameters["type_id"] = cal_event._type_id
        url_parameters["record_id"] = cal_event._record_id
        event = icalendar.Event()
        hashworker = hashlib.new("md5")
        hashworker.update(cal_event.get_id().encode())
        event.add(
            "uid",
            hashworker.hexdigest() + "." + repo_string_for_uid + "@" + settings.DATATIG_HUB_DOMAIN,
        )
        # TODO base class should have methods to get datetime, and with right timezone too
        event.add("DTSTART", datetime.datetime.fromtimestamp(cal_event.get_start_timestamp()))
        event.add("DTEND", datetime.datetime.fromtimestamp(cal_event.get_end_timestamp()))
        url = (
            "http"
            + ("s" if settings.DATATIG_HUB_HTTPS else "")
            + "://"
            + settings.DATATIG_HUB_DOMAIN
            + django.urls.reverse(url_path_name, kwargs=url_parameters)
        )
        event.add("SUMMARY", cal_event.get_summary())
        event.add("URL", url)
        event.add("DESCRIPTION", url)
        calendar.add_component(event)
    return calendar.to_ical()
