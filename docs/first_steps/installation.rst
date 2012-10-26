.. _installation:

Installation
============

Requirements
------------

- Python 2.6 or 2.7
- virtualenv_
- ``build_essential`` and ``python-dev`` (on Debian or Ubuntu)
- or ``Xcode`` (on OSX)
- Includes support for PostgreSQL, MySQL and SQLite (tested regularly), and a
  list of `other SQL databases`_. SQLite is available in the default install,
- Includes support for PostgreSQL, MySQL and SQLite (tested regularly), and 
  `other SQL databases`_. SQLite is available in the default install,
  so may be used for easy development, and may prove to be adequate for some
  deployments. However, Kotti is flexible for installation of your choice of
  database during development or at deployment.
- Kotti takes advantage of Pyramid's WSGI server called Waitress, as
  a default server. Install other WSGI servers such as Apache and Nginx as
  needed. See the Pyramid documentation for a variety of server and server
  configuration options.

Installation using ``virtualenv``
---------------------------------

It is recommended to install Kotti inside a virtualenv:

.. code-block:: bash

  virtualenv mysite
  cd mysite
  bin/pip install -r https://raw.github.com/Pylons/Kotti/0.7.2/requirements.txt

Kotti uses `Paste Deploy`_ for configuration and deployment.  An
example configuration file is included with Kotti's source
distribution.  Download it to your virtualenv directory (mysite):

.. code-block:: bash

  wget https://github.com/Pylons/Kotti/raw/master/app.ini

Run Kotti using this default app configuration:

.. code-block:: bash

  bin/pserve app.ini

The bin/pserve command will run Waitress as the default development server.
You will see console output giving the local URL to view the site.

.. _other SQL databases: http://www.sqlalchemy.org/docs/core/engines.html#supported-databases
.. _variety of web servers: http://wsgi.org/wsgi/Servers
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _Paste Deploy: http://pythonpaste.org/deploy/#the-config-file
