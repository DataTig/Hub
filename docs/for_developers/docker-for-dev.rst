Docker for dev
==============

These instructions assume a Linux development environment. They probably work on a Mac. They won't work on Windows.

Setup
-----

To setup:

.. code-block::

    cp docker-compose.dev.env.template docker-compose.dev.env

Edit `docker-compose.dev.env`

Edit your dev machine's hosts file and set:

.. code-block::

    127.0.0.1  dev.hub.datatig.com


Run
---

To run:

.. code-block::

   docker compose -f docker-compose.dev.yml up --remove-orphans


You can then visit: http://dev.hub.datatig.com:8000/

Running commands
----------------

Make sure environment is running (see up command above).

To run a Django manage command:

.. code-block::

    docker compose -f docker-compose.dev.yml run -w /app/datatighub datatig-hub-app-dev python manage.py

To get a bash shell in a container:

.. code-block::

    docker compose -f docker-compose.dev.yml run -w /app datatig-hub-app-dev /bin/bash


Look in DB
----------

.. code-block::

    docker compose -f docker-compose.dev.yml run datatig-hub-postgres su -c 'PGPASSWORD=1234 psql   -U postgres -h datatig-hub-postgres app'


Python Packages Upgrade
-----------------------

This will upgrade all packages:


.. code-block::

    docker compose -f docker-compose.dev.yml run datatig-hub-app-dev  pip-compile --upgrade
    docker compose -f docker-compose.dev.yml run datatig-hub-app-dev  pip-compile --upgrade requirements_dev.in
    docker compose -f docker-compose.dev.yml run datatig-hub-app-dev  pip-compile --upgrade requirements_docs.in
    docker compose -f docker-compose.dev.yml down # (if running)
    docker compose -f docker-compose.dev.yml build --no-cache
    docker compose -f docker-compose.docs.yml down # (if running)
    docker compose -f docker-compose.docs.yml build --no-cache

Test
----

.. code-block::

    docker compose -f docker-compose.dev.yml run -e DATATIG_HUB_CELERY_BROKER_URL=memory:// -e DATATIG_HUB_DATA_STORAGE_V1=/tmp -w /app/datatighub datatig-hub-app-dev pytest


Lint
----

.. code-block::

    docker compose -f docker-compose.dev.yml run -w /app/datatighub datatig-hub-app-dev isort .
    docker compose -f docker-compose.dev.yml run -w /app/datatighub datatig-hub-app-dev black .
    docker compose -f docker-compose.dev.yml run -w /app/datatighub datatig-hub-app-dev flake8 .
    docker compose -f docker-compose.dev.yml run -w /app/datatighub datatig-hub-app-dev mypy --install-types --non-interactive .
    sudo chown -R `whoami`:`id -g` datatighub/


# TODO get rid of the chown by seting user in docker build to be same user


Restarting app server and worker without also restarting database and message queue server
------------------------------------------------------------------------------------------

If you change code, you may need to restart the app or worker. This will do so quickly:

.. code-block::

    docker compose -f docker-compose.dev.yml  restart datatig-hub-app-dev && docker compose -f docker-compose.dev.yml  restart datatig-hub-worker-dev


Docs
----

Run:

.. code-block::

    docker compose -f docker-compose.docs.yml up

Go to: http://localhost:5000

Sometimes the auto build process does not pick up on new changes. In this case, stop and restart the command above and everything will be rebuilt.

Deleting data and starting again
--------------------------------

.. code-block::

    docker compose -f docker-compose.dev.yml down
    docker system prune -f
    docker volume rm datatig-hub_datatig_hub_data
    docker volume rm datatig-hub_datatig_hub_postgres

Deleting and restore from backup
--------------------------------

Get backup file, put in top directory of this repository. Run as root (change number to date of backup):

.. code-block::

    unzip backup-XX.zip
    docker compose -f docker-compose.dev.yml down
    docker system prune -f
    docker volume rm datatig-hub_datatig_hub_data
    docker volume rm datatig-hub_datatig_hub_postgres
    docker compose -f docker-compose.dev.yml up

In separate prompt (change number to date of backup):


.. code-block::

    docker compose -f docker-compose.dev.yml run datatig-hub-app-dev cp -r home/datatighub/data/v1 /data/
    docker compose -f docker-compose.dev.yml run datatig-hub-postgres  su -c 'PGPASSWORD=1234 psql -d app -U postgres -h datatig-hub-postgres -f  /app/home/datatighub/backups/database-XX.sql'
    rm -rf home/datatighub
    rmdir home
