Building a payment processor
##################################

Install requirements
^^^^^^^^^^^^^^^^^^^^^

Uses Python 3.4.3 and up.

Install OS requirements

.. code:: python

    sudo apt install libxml2-dev libxmlsec1-dev libxmlsec1-openssl default-libmysqlclient-dev


To install requirements use the following command:

.. code:: python

    pip install -r requirements.txt --find-links=libraries


Create your environment file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extra settings file are loaded like this

.. code:: python

    exec('from .host_settings.{} import *'.format(HOST_NAME))

So you need to create a file on 'core_payments.host_settings.<your host name>', you
can use ``hostname`` command to know your hostname

**Suggestion:** Copy the content of core_payments/host_settings/example.pu on
core_payments/host_settings/<your host name>.py

Docker database file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you haven't a mysql database installation you could use a docker example on docker folder
to create a mysql and phpmyadmin installation faster with docker.


Run the project
^^^^^^^^^^^^^^^^^^^^^
Just run this code on core_payments

.. code:: python

    python manage.py runserver 127.0.0.1:8812

Run the tests
^^^^^^^^^^^^^^^^^

Before start coding run all tests

.. code:: python

    python manage.py test

User needs to create databases on database server, if you use docker file to build your installations you should need to run

  REVOKE ALL PRIVILEGES ON *.* FROM 'user'@'%';
  GRANT ALL PRIVILEGES ON *.* TO 'user'@'%' REQUIRE NONE WITH GRANT OPTION MAX_QUERIES_PER_HOUR 0 MAX_CONNECTIONS_PER_HOUR 0 MAX_UPDATES_PER_HOUR 0 MAX_USER_CONNECTIONS 0;

Note: this is for testing and developing propuses.