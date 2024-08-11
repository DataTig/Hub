Settings
========

Settings are configured by environmental variables.

DATATIG_HUB_DATABASE_NAME
-------------------------

Postgres database name.

DATATIG_HUB_DATABASE_USER
-------------------------

Postgres database user.

DATATIG_HUB_DATABASE_PASSWORD
-----------------------------

Postgres database password.

DATATIG_HUB_DATABASE_HOST
-------------------------

Postgres database host.

DATATIG_HUB_CELERY_BROKER_URL
-----------------------------

DATATIG_HUB_NAME
----------------

The name of the site, used in page headers, titles and footers. eg "My DataTig Host"

DATATIG_HUB_EMAIL
-----------------

A contact email address that will be made public on the site.

DATATIG_HUB_META_ROBOTS
-----------------------

Should be `nofollow, noindex`, `follow, index` or something similiar.

Will be used on main pages of site only.

(Each Repository currently does not allow follow or index at all (but might have it's own setting for this in the future)

DATATIG_HUB_DOMAIN
------------------

DATATIG_HUB_HTTPS
-----------------

A boolean, `true` or `false`.

DATATIG_HUB_SECRET_KEY
----------------------

https://docs.djangoproject.com/en/5.0/ref/settings/#std-setting-SECRET_KEY

DATATIG_HUB_DATA_STORAGE_V1
---------------------------

DATATIG_HUB_STATIC_ROOT
-----------------------

https://docs.djangoproject.com/en/5.0/ref/settings/#static-root

DATATIG_HUB_GITHUB_OAUTH_APP_CLIENT_ID
--------------------------------------

For :doc:`more details see here<github-oauth-apps>`.

DATATIG_HUB_GITHUB_OAUTH_APP_CLIENT_SECRET
------------------------------------------

For :doc:`more details see here<github-oauth-apps>`.

DATATIG_HUB_SENTRY_DSN
----------------------

A DSN string for Sentry  - see https://sentry.io/

DATATIG_HUB_SESSION_FILE_PATH
-----------------------------

Where Django stores session files. 

DATATIG_HUB_LINK_CHECKER_ENABLED
--------------------------------

DATATIG_HUB_LINK_CHECKER_SECONDS_TILL_CHECK_URL_AGAIN
-----------------------------------------------------

DATATIG_HUB_LINK_CHECKER_SECONDS_TILL_CHECK_ROBOTS_TXT_AGAIN
------------------------------------------------------------

DATATIG_HUB_LINK_CHECKER_ROBOTS_TXT_CACHE_SIZE
----------------------------------------------

DATATIG_HUB_LINK_CHECKER_USER_AGENT
-----------------------------------


