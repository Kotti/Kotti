.. _instalation:

Installation
============

Requirements
------------

- Runs on Python versions 2.6 and 2.7.
- Support for PostgreSQL and SQLite (tested regularly), and a list of
  `other SQL databases`_
- Support for WSGI and a `variety of web servers`_, including Apache

Installation using ``virtualenv``
---------------------------------

It's recommended to install Kotti inside a virtualenv_:

.. code-block:: bash

  virtualenv mysite --no-site-packages
  cd mysite
  bin/pip install Kotti

Kotti uses `Paste Deploy`_ for configuration and deployment.  An
example configuration file is included with Kotti's source
distribution.  Download it:

.. code-block:: bash

  wget https://github.com/Pylons/Kotti/raw/master/app.ini

Finally, to run Kotti:

.. code-block:: bash

  bin/pserve app.ini

.. note::

  To run the application with older versions of Pyramid, you might
  need to do instead:

  .. code-block:: bash
  
    bin/pip install PasteScript
    bin/paster serve app.ini

.. _other SQL databases: http://www.sqlalchemy.org/docs/core/engines.html#supported-databases
.. _variety of web servers: http://wsgi.org/wsgi/Servers
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _Paste Deploy: http://pythonpaste.org/deploy/#the-config-file
