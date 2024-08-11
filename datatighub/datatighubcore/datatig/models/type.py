from datatig.models.type import TypeModel
from django.http import QueryDict


class HubTypeModel(TypeModel):

    def get_records_filter(self):
        return HubTypeRecordsFilterModel(self)


class HubTypeRecordsFilterModel:

    def __init__(self, type):
        self._type = type
        self._number_on_page = 100
        self._page = 1
        self._columns = []
        self._results_records = None
        self._results_records_meta = None
        self._id_contains = ""
        self._field_filters = {}

    def load_default(self, number_on_page=100):
        self._number_on_page = number_on_page
        self._columns = self._type.get_list_fields()

    def load_from_request(self, request, number_on_page=100):
        self._number_on_page = number_on_page
        self._page = max(1, int(request.GET.get("page", "1")))
        self._columns = [
            fn for fn in request.GET.getlist("columns") if self._type.get_field(fn)
        ] or self._type.get_list_fields()
        self._id_contains = request.GET.get("id_value", "")
        for key in request.GET:
            if key.startswith("field_"):
                key_bits = key[6:].split("___", maxsplit=2)
                if not key_bits[0] in self._field_filters:
                    self._field_filters[key_bits[0]] = {}
                self._field_filters[key_bits[0]][key_bits[1]] = request.GET.get(key)

    def get_columns(self):
        return self._columns

    def get_number_on_page(self):
        return self._number_on_page

    def get_page(self):
        return self._page

    def get_id_contains(self):
        return self._id_contains

    def get_field_filters_for_field_id(self, field_id):
        return self._field_filters.get(field_id, {})

    def process(self, sqlite_db):
        self._results_records, self._results_records_meta = sqlite_db.get_records(self._type.get_id(), self)

    def get_results_records(self):
        return self._results_records

    def get_results_records_meta(self):
        return self._results_records_meta

    def get_paging_links(self):
        paging_links = []
        qd = QueryDict().copy()
        qd.setlist("columns", self._columns)
        if self._id_contains:
            qd["id_value"] = self._id_contains
        for k1, v_bit in self._field_filters.items():
            for k2, v in v_bit.items():
                if v:
                    qd["field_" + k1 + "___" + k2] = v
        for i in range(1, self._results_records_meta["total_pages"] + 1):
            qd["page"] = str(i)
            paging_links.append(
                {
                    "text": str(i),
                    "link": "?" + qd.urlencode(),
                }
            )
        return paging_links
