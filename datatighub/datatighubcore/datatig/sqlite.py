from contextlib import closing

from datatig.models.field import FieldConfigModel
from datatig.models.record import RecordModel
from datatig.models.type import TypeModel
from datatig.sqlite import DataStoreSQLite


class HubDatatigSqlite(DataStoreSQLite):

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self._connection.close()

    def query(self, sql, params):
        with closing(self._connection.cursor()) as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def get_records(self, type_id, filter):
        # make Search from filter
        where_sql = []
        sql_params = []
        if filter.get_id_contains():
            where_sql.append("ID LIKE ?")
            sql_params.append("%" + filter.get_id_contains() + "%")
        for field_id, field in self._site_config.get_type(type_id).get_fields().items():
            field_filters = filter.get_field_filters_for_field_id(field_id)

            if field.get_type() == "string":
                if field_filters.get("value"):
                    where_sql.append("field_" + field_id + " LIKE ?")
                    sql_params.append("%" + field_filters.get("value") + "%")

        # Now Get
        out = []
        meta = {}
        with closing(self._connection.cursor()) as cur:
            cur.execute(
                "SELECT COUNT(*) AS c FROM record_"
                + type_id
                + (" WHERE " + " AND ".join(where_sql) if where_sql else ""),
                sql_params,
            )
            meta["count_all"] = cur.fetchone()["c"]
            cur.execute(
                "SELECT * FROM record_{type} {where} ORDER BY {order} id ASC LIMIT {limit} OFFSET {offset}".format(
                    type=type_id,
                    where=(" WHERE " + " AND ".join(where_sql) if where_sql else ""),
                    limit=filter.get_number_on_page(),
                    offset=(filter.get_page() - 1) * filter.get_number_on_page(),
                    order="",
                ),
                sql_params,
            )
            for data in cur.fetchall():
                record = RecordModel(type=self._site_config.get_type(type_id), id=data["id"])
                record.load_from_database(
                    data,
                    # TODO No errors data is loaded with this method!
                    errors_data=[],
                )
                out.append(record)
        meta["total_pages"] = max(1, int(meta["count_all"] / filter.get_number_on_page()))
        return out, meta

    def get_field_stats(self, type: TypeModel, field: FieldConfigModel):
        out = {}
        with closing(self._connection.cursor()) as cur:
            # Total Records
            if field.get_type() != "list-dictionaries":
                cur.execute("SELECT COUNT(*) AS c FROM record_" + type.get_id())
                out["records"] = cur.fetchone()["c"]
            # Records with value
            if field.get_type() in ["string", "url"]:
                cur.execute(
                    "SELECT COUNT(*) AS c FROM record_"
                    + type.get_id()
                    + " WHERE field_"
                    + field.get_id()
                    + "  IS NOT NULL OR field_"
                    + field.get_id()
                    + " != '' "
                )
                out["records_with_value"] = cur.fetchone()["c"]
                out["records_with_value_percentage"] = out["records_with_value"] / out["records"] * 100
            elif field.get_type() in ["boolean"]:
                # Value
                cur.execute(
                    "SELECT COUNT(*) AS c FROM record_"
                    + type.get_id()
                    + " WHERE field_"
                    + field.get_id()
                    + "  IS NOT NULL"
                )
                out["records_with_value"] = cur.fetchone()["c"]
                out["records_with_value_percentage"] = out["records_with_value"] / out["records"] * 100
                # True
                cur.execute(
                    "SELECT COUNT(*) AS c FROM record_" + type.get_id() + " WHERE field_" + field.get_id() + "=true"
                )
                out["records_with_true_value"] = cur.fetchone()["c"]
                out["records_with_true_value_percentage"] = out["records_with_true_value"] / out["records"] * 100
                # False
                cur.execute(
                    "SELECT COUNT(*) AS c FROM record_" + type.get_id() + " WHERE field_" + field.get_id() + "=false"
                )
                out["records_with_false_value"] = cur.fetchone()["c"]
                out["records_with_false_value_percentage"] = out["records_with_false_value"] / out["records"] * 100

            # Number of sub records per record
            if field.get_type() in ["list-strings", "list-dictionaries"]:
                try:
                    cur.execute(
                        """SELECT  d.src, COUNT(d.id) AS rc
                            FROM (
                            SELECT r.id, count(sr.record_id) AS src
                            FROM record_{type} AS r
                            LEFT JOIN record_{type}___field_{field} AS sr ON sr.record_id = r.id
                            GROUP BY r.id) AS d
                            GROUP BY d.src""".format(
                            type=type.get_id(),
                            field=field.get_id(),
                        )
                    )
                    data = {r["src"]: r["rc"] for r in cur.fetchall()}
                    out["records_with_number_values"] = {
                        "min_key": min(data.keys()),
                        "max_key": min(data.keys()),
                        "data": data,
                    }
                except Exception:
                    # Some data is an older format with different table names, so errors are expected.
                    pass
            # Distinct values in field
            if field.get_type() in ["string"]:
                cur.execute(
                    (
                        "SELECT field_{field} AS value, COUNT(*) AS c FROM record_{type} "
                        + "WHERE field_{field} IS NOT NULL OR field_{field} != '' "
                        + "GROUP BY field_{field} ORDER BY c DESC"
                    ).format(field=field.get_id(), type=type.get_id())
                )
                distinct_values = cur.fetchall()
                if distinct_values and distinct_values[0]["c"] > 1:
                    out["distinct_values"] = distinct_values
            elif field.get_type() in ["list-strings"]:
                try:
                    cur.execute(
                        (
                            "SELECT value, COUNT(*) AS c FROM record_{type}___field_{field} "
                            + "GROUP BY value ORDER BY c DESC"
                        ).format(field=field.get_id(), type=type.get_id())
                    )
                    distinct_values = cur.fetchall()
                    if distinct_values and distinct_values[0]["c"] > 1:
                        out["distinct_values"] = distinct_values
                except Exception:
                    # Some data is an older format with different table names, so errors are expected.
                    pass
        return out

    def get_url_field_values(self):
        urls = set()
        for type_id, type in self._site_config.get_types().items():
            records, meta = self.get_records(type_id, type.get_records_filter())
            for record in records:
                for field_id, field in type.get_fields().items():
                    if field.get_type() == "url":
                        value = record.get_field_value(field_id)
                        if value.get_value():
                            urls.add(value.get_value())
                    elif field.get_type() == "list-dictionaries":
                        pass  # TODO
        return list(urls)
