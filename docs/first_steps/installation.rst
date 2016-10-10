.. _installation:

Installation
============

Requirements
------------

- Python 2.7 (Python 3 will be supported soon)
- virtualenv_
- ``build_essential`` and ``python-dev`` (on Debian or Ubuntu) or
- ``Xcode`` (on OS X) or
- equivalent build toolchain for your OS.

Installation using ``virtualenv``
---------------------------------

It is recommended to install Kotti inside a virtualenv:

.. parsed-literal::

  virtualenv mysite
  cd mysite
  bin/pip install -r https://raw.github.com/Kotti/Kotti/stable/requirements.txt
  bin/pip install Kotti

This will install the latest released version of Kotti and all its requirements into your virtualenv.

Kotti uses `Paste Deploy`_ for configuration and deployment.
An example configuration file is included with Kotti's source distribution.
Download it to your virtualenv directory (mysite):

.. parsed-literal::

  wget https://raw.github.com/Kotti/Kotti/stable/app.ini

See the list of `Kotti tags`_, perhaps to find the latest released version.
You can search the `Kotti listing on PyPI`_ also, for the latest Kotti release (Kotti with a capital K is Kotti itself, kotti_this and kotti_that are add-ons in the list on PyPI).

.. _Kotti tags: https://github.com/Kotti/Kotti/tags
.. _Kotti listing on PyPI: https://pypi.python.org/pypi?%3Aaction=search&term=kotti&submit=search

To run Kotti using the ``app.ini`` example configuration file:

.. code-block:: bash

  bin/pserve app.ini

This command runs Waitress, Pyramid's WSGI server, which Kotti uses as a default server.
You will see console output giving the local URL to view the site in a browser.

As you learn more, install other servers, with WSGI enabled, as needed.
For instance, for Apache, you may install the optional mod_wsgi module, or for Nginx, you may use choose to use uWSGI.
See the Pyramid documentation for a variety of server and server configuration options.

The pserve command above uses SQLite as the default database.
On first run, Kotti will create a SQLite database called Kotti.db in your mysite directory.
Kotti includes support for PostgreSQL, MySQL and SQLite (tested regularly), and
`other SQL databases`_.
The default use of SQLite makes initial development easy.
Although SQLite may prove to be adequate for some deployments, Kotti is flexible for installation of your choice of database during development or at deployment.

Installation using Docker (experimental)
----------------------------------------

This assumes that you already have Docker_ installed:

.. parsed-literal::

  docker pull kotti/kotti
  docker run -i -t -p 5000:5000 kotti/kotti

This should get you a running Kotti instance on port 5000.

.. _other SQL databases: http://www.sqlalchemy.org/docs/core/engines.html#supported-databases
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _Paste Deploy: http://pythonpaste.org/deploy/#the-config-file
.. _Docker: http://docker.io/
