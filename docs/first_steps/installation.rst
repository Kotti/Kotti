.. _installation:

Installation
============

Requirements
------------

- Python 2.6 or 2.7
- virtualenv_
- ``build_essential`` and ``python-dev`` (on Debian or Ubuntu)
- or ``Xcode`` (on OSX)

Installation using ``virtualenv``
---------------------------------

It is recommended to install Kotti inside a virtualenv:

.. code-block:: bash

  virtualenv mysite
  cd mysite
  bin/pip install -r https://raw.github.com/Kotti/Kotti/0.7.2/requirements.txt

Kotti uses `Paste Deploy`_ for configuration and deployment.  An
example configuration file is included with Kotti's source
distribution.  Download it to your virtualenv directory (mysite):

.. code-block:: bash

  wget https://github.com/Kotti/Kotti/raw/master/app.ini

To run Kotti using this example configuration file:

.. code-block:: bash

  bin/pserve app.ini

This command runs Waitress, Pyramid's WSGI server, which Kotti uses as a
default server.  You will see console output giving the local URL to view the
site in a browser.

As you learn more, install other servers, with WSGI enabled, as needed. For
instance, for Apache, you may install the optional mod_wsgi module, or for
Nginx, you may use choose to use uWSGI.  See the Pyramid documentation for a
variety of server and server configuration options.

The pserve command above uses SQLite as the default database. On first run,
Kotti will create a SQLite database called Kotti.db in your mysite directory.

Kotti includes support for PostgreSQL, MySQL and SQLite (tested regularly), and
`other SQL databases`_. The default use of SQLite makes initial development
easy.  Although SQLite may prove to be adequate for some deployments, Kotti is
flexible for installation of your choice of database during development or at
deployment.

.. _other SQL databases: http://www.sqlalchemy.org/docs/core/engines.html#supported-databases
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _Paste Deploy: http://pythonpaste.org/deploy/#the-config-file
