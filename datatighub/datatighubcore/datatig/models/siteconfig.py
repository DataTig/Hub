import json
import sqlite3
from contextlib import closing

from datatig.models.calendar import CalendarModel
from datatig.models.siteconfig import SiteConfigModel

from .type import HubTypeModel


class HubSiteConfigModel(SiteConfigModel):

    def load_from_sqlite_database(self, sqlite_file_name):
        type_json_schema = {}
        with sqlite3.connect(sqlite_file_name) as connection:
            connection.row_factory = sqlite3.Row
            with closing(connection.cursor()) as cur:
                self._config: dict = {"types": [], "calendars": {}}
                # types
                cur.execute("SELECT * FROM type", [])
                type_rows = cur.fetchall()
                for type_row in type_rows:
                    type = {
                        "id": type_row["id"],
                        "directory": type_row["directory"],
                        "list_fields": json.loads(type_row["list_fields"]),
                        "pretty_json_indent": type_row["pretty_json_indent"],
                        "default_format": type_row["default_format"],
                        "markdown_body_is_field": type_row["markdown_body_is_field"],
                        "fields": [],
                    }
                    type_json_schema[type_row["id"]] = json.loads(type_row["json_schema"])
                    cur.execute(
                        "SELECT * FROM type_field WHERE type_id=? ORDER BY sort ASC",
                        [type_row["id"]],
                    )
                    for field_row in cur:
                        type_field_json = {
                            "id": field_row["id"],
                            "type": field_row["type"],
                            "key": field_row["key"],
                            "title": field_row["title"],
                            "description": field_row["description"],
                        }
                        type_field_json.update(json.loads(field_row["extra_config"]))
                        if "/" in field_row["id"]:
                            type_field_json["id"] = field_row["id"].split("/")[-1]
                            if "fields" in type["fields"][-1]:
                                type["fields"][-1]["fields"].append(type_field_json)
                            else:
                                type["fields"][-1]["fields"] = [type_field_json]
                        else:
                            type["fields"].append(type_field_json)
                    self._config["types"].append(type)
                # calendars
                cur.execute("SELECT * FROM calendar", [])
                calendar_rows = cur.fetchall()
                for calendar_row in calendar_rows:
                    calendar = {"timezone": calendar_row["timezone"]}
                    self._config["calendars"][calendar_row["id"]] = calendar
        # after load
        self._after_load()
        # Add things to loaded models
        for type_id, type in self._types.items():
            type._cached_json_schema = type_json_schema[type_id]

    def _after_load(self):
        # Only copied as I need to change the class of the TypeModel used
        for type_config in self._config.get("types", []):
            type_config_model = HubTypeModel(self)
            type_config_model.load_from_config(type_config)
            self._types[type_config_model.get_id()] = type_config_model
        for calendar_id, calendar_config in self._config.get("calendars", {}).items():
            calendar_config_model = CalendarModel(self)
            calendar_config_model.load_from_config(calendar_id, calendar_config)
            self._calendars[calendar_id] = calendar_config_model
