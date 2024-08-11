API
===

Each repository has a JSON API.

"API" buttons are available on many pages to take you straight to the relevant section

Repository Tree API
-------------------

Available at:

* `/g/SLUG/tree/TREE/api1.json`
* `/gh/OWNER/REPOSITORY/tree/TREE/api1.json`

Type API
--------

Available at:

* `/g/SLUG/tree/TREE/type/TYPE/api1.json`
* `/gh/OWNER/REPOSITORY/tree/TREE/type/TYPE/api1.json`

Records List API
----------------

Available at:

* `/g/SLUG/tree/TREE/type/TYPE/record_api1.json`
* `/gh/OWNER/REPOSITORY/tree/TREE/type/TYPE/record_api1.json`

These end points accept the same filtering parameters as the web interface.

So for example if you perform a record search on the web interface and get a URL with the options
(eg includes `?id_value=gb`), you can copy all those options on the end of this API point.
(eg `/gh/OWNER/REPOSITORY/tree/TREE/type/TYPE/record_api1.json?id_value=gb`)

Record API
----------

Available at:

* `/gh/OWNER/REPOSITORY/tree/TREE/type/TYPE/record/RECORD/api1.json`
* `/g/SLUG/tree/TREE/type/TYPE/record/RECORD/api1.json`


