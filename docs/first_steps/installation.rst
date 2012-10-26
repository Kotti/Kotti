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
  list of `other SQL databases`_. SQLite may be used for easy development, and
  for many use cases. Install other databases as needed.
- Kotti takes advantage of Pyramid's built-in WSGI server called Waitress, as
  a default server. Install other WSGI servers such as Apache and Nginx as
  needed.

Installation using ``virtualenv``
---------------------------------

It is recommended to install Kotti inside a virtualenv:

.. code-block:: bash

  virtualenv mysite
  cd mysite
  bin/pip install -r https://raw.github.com/Pylons/Kotti/0.7.2/requirements.txt

Kotti uses `Paste Deploy`_ for configuration and deployment.  An
example configuration file is included with Kotti's source
distribution.  Download it to your project directory (mysite):

.. code-block:: bash

  wget https://github.com/Pylons/Kotti/raw/master/app.ini

Run Kotti using this default app configuration, with:

.. code-block:: bash

  bin/pserve app.ini

The bin/pserve command will run Waitress as the default development server.

.. _other SQL databases: http://www.sqlalchemy.org/docs/core/engines.html#supported-databases
.. _variety of web servers: http://wsgi.org/wsgi/Servers
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _Paste Deploy: http://pythonpaste.org/deploy/#the-config-file
