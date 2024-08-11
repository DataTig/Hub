Install
=======

Needed libraries
----------------

Run as root:

.. code-block::

    apt-get update
    apt-get install -y python3 python3-virtualenv git sqlite3 sqlite-utils python3-postgresql libpq-dev python3-dev psmisc


Postgres
--------

Run as root:

.. code-block::

    apt-get install -y postgresql-15
    su -c "psql -c \"CREATE USER datatighub WITH NOCREATEDB PASSWORD 'insert-random-db-password-here' \""  postgres
    su -c "psql -c \"CREATE DATABASE datatighub WITH OWNER=datatighub    \""  postgres


Redis
-----

(v7.0 in Debian 12 Bookworm, so under old license.)

Run as root:

.. code-block::

    apt-get install -y redis-server


Create user
-----------

Run as root:

.. code-block::

    adduser datatighub


Create Datastore
----------------

Run as root:

.. code-block::

    mkdir -p /home/datatighub/data/v1
    chown -R datatighub:datatighub /home/datatighub/data


Create Webroot
--------------

Run as root:

.. code-block::

    mkdir -p /home/datatighub/webroot/static
    chown -R datatighub:datatighub /home/datatighub/webroot
    chmod a+rx /home/datatighub/
    chmod -R a+rx /home/datatighub/webroot/
    touch /home/datatighub/webroot/robots.txt


Edit `/home/datatighub/webroot/robots.txt` to suit. 

Do not just deny all robots everywhere tho, 
as this will block legitimate robots (like the robot Google Calendar uses to import ical feeds).

Create Session Filepath
-----------------------

.. code-block::

    mkdir -p /home/datatighub/sessions
    chown -R datatighub:datatighub /home/datatighub/sessions


Source Code & Virtual Env
-------------------------

Run as root:

.. code-block::

    su datatighub


Then:

.. code-block::

    cd
    git clone https://github.com/DataTig/Hub.git datatighub
    cd datatighub/
    python3 -m virtualenv .ve
    exit


Environmental variables
-----------------------

Create file `/home/datatighub/env_vars` and set and then edit the contents:


.. code-block::

    DATATIG_HUB_DATABASE_NAME=datatighub
    DATATIG_HUB_DATABASE_USER=datatighub
    DATATIG_HUB_DATABASE_PASSWORD=insert-random-db-password-here
    DATATIG_HUB_DATABASE_HOST=localhost
    DATATIG_HUB_CELERY_BROKER_URL=redis://localhost
    DATATIG_HUB_NAME=Dev Server
    DATATIG_HUB_EMAIL=test@example.com
    DATATIG_HUB_META_ROBOTS=noindex, nofollow
    DATATIG_HUB_DOMAIN=example.com
    DATATIG_HUB_HTTPS=false
    DATATIG_HUB_SECRET_KEY=django-insecure-insert-random-key-here
    DATATIG_HUB_DATA_STORAGE_V1=/home/datatighub/data/v1/
    DATATIG_HUB_STATIC_ROOT=/home/datatighub/webroot/static
    DATATIG_HUB_GITHUB_OAUTH_APP_CLIENT_ID=
    DATATIG_HUB_GITHUB_OAUTH_APP_CLIENT_SECRET=
    DATATIG_HUB_SENTRY_DSN=
    DATATIG_HUB_SESSION_FILE_PATH=/home/datatighub/sessions

No quotes around values.


For :doc:`more details of what you need to edit see here<../../for_sysadmins/settings>`.

UWSGI
-----

Run as root:

.. code-block::

    apt-get install -y uwsgi  uwsgi-plugin-python3
    cp /home/datatighub/datatighub/host_on_vm/datatighub.ini /etc/uwsgi/apps-available/datatighub.ini
    ln -s /etc/uwsgi/apps-available/datatighub.ini /etc/uwsgi/apps-enabled/datatighub.ini


Apache
------

Create file `/etc/apache2/sites-available/datatighub.conf` and set the contents:

.. code-block::

    <VirtualHost *:80>
        ServerName localhost
        Include /etc/apache2/sites-available/datatighub.conf.include
    </VirtualHost>


Run as root:

.. code-block::

    apt-get install -y apache2
    cp /home/datatighub/datatighub/host_on_vm/datatighub.conf.include /etc/apache2/sites-available/datatighub.conf.include
    a2enmod proxy_uwsgi
    a2ensite datatighub
    systemctl  restart apache2


Upgrade Script
--------------

Run as root:

.. code-block::

    cp /home/datatighub/datatighub/host_on_vm/update_as_datatighub.sh /home/datatighub/update_as_datatighub.sh
    chown datatighub:datatighub /home/datatighub/update_as_datatighub.sh
    chmod u+x /home/datatighub/update_as_datatighub.sh

    cp /home/datatighub/datatighub/host_on_vm/update_as_root.sh /home/datatighub/update_as_root.sh
    chown root:root /home/datatighub/update_as_root.sh
    chmod u+x /home/datatighub/update_as_root.sh


Worker in systemd
-----------------

Run as root:

.. code-block::

    cp /home/datatighub/datatighub/host_on_vm/run_worker.sh /home/datatighub/run_worker.sh
    chown datatighub:datatighub /home/datatighub/run_worker.sh
    chmod u+x /home/datatighub/run_worker.sh

    cp /home/datatighub/datatighub/host_on_vm/datatighubworker.service /etc/systemd/system/datatighubworker.service
    systemctl enable datatighubworker.service

    cp /home/datatighub/datatighub/host_on_vm/run_worker_important.sh /home/datatighub/run_worker_important.sh
    chown datatighub:datatighub /home/datatighub/run_worker_important.sh
    chmod u+x /home/datatighub/run_worker_important.sh

    cp /home/datatighub/datatighub/host_on_vm/datatighubworkerimportant.service /etc/systemd/system/datatighubworkerimportant.service
    systemctl enable datatighubworkerimportant.service


Set up app
----------

Run as root:

.. code-block::

    su -c "/home/datatighub/update_as_datatighub.sh" datatighub
    /home/datatighub/update_as_root.sh


Cron
----

Run as root:

.. code-block::

    cp /home/datatighub/datatighub/host_on_vm/cron.sh /home/datatighub/cron.sh
    chown datatighub:datatighub /home/datatighub/cron.sh
    chmod u+x /home/datatighub/cron.sh


Change to user with `su datatighub`
Edit cron with `crontab -e`
Add `0 2 * * * /home/datatighub/cron.sh`

SSL
---


Run as root:

.. code-block::


    apt-get install -y certbot python3-certbot-apache
    certbot -d server-domain


Follow prompts


Then in `env_vars` set

.. code-block::

    DATATIG_HUB_HTTPS=true


Set up python run_manage command
--------------------------------

Run as root:

.. code-block::

    cp /home/datatighub/datatighub/host_on_vm/run_manage.sh /home/datatighub/run_manage.sh
    chown datatighub:datatighub /home/datatighub/run_manage.sh
    chmod u+x /home/datatighub/run_manage.sh


Superuser for admin UI
----------------------

Run as root:

.. code-block::

    su datatighub


Then:


.. code-block::

    ./run_manage.sh createsuperuser


Follow prompts, then `exit` back to root user.

Backups
-------


Create file `/home/datatighub/.pgpass` and set the contents:

.. code-block::

    localhost:5432:datatighub:datatighub:insert-random-db-password-here


Run as root:

.. code-block::


    apt-get install -y zip

    chown datatighub:datatighub /home/datatighub/.pgpass
    chmod 600 /home/datatighub/.pgpass

    mkdir /home/datatighub/backups
    chown datatighub:datatighub /home/datatighub/backups

    cp /home/datatighub/datatighub/host_on_vm/backup.sh /home/datatighub/backup.sh
    chown datatighub:datatighub /home/datatighub/backup.sh
    chmod u+x /home/datatighub/backup.sh


Change to user with `su datatighub`
Edit cron with `crontab -e`
Add `0 4 * * * /home/datatighub/backup.sh`

This only creates zip files and leaves them on the same virtual machine!
You need to make sure these files are copied and backed up to a secure location elsewhere!
