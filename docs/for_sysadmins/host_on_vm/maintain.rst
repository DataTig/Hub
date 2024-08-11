Maintain
========

Update app
----------

Run as root:

.. code-block::

    su -c "/home/datatighub/update_as_datatighub.sh" datatighub
    /home/datatighub/update_as_root.sh

Run a Django manage command
---------------------------

Run as root:

.. code-block::

    su datatighub

Then:

.. code-block::

    ~/run_manage.sh

Access Database
---------------

Run as root:

.. code-block::

    su datatighub

Then:

.. code-block::

    psql -U datatighub datatighub


