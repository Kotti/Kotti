Requirements
------------

- Runs on Python versions 2.6 and 2.7.
- Support for PostgreSQL and SQLite (tested continuously), and a list of `other SQL databases`_ (not tested regularly)
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
distribution:

.. code-block:: bash

  wget https://github.com/Pylons/Kotti/raw/master/development.ini

Finally, to run the application:

.. code-block:: bash

  bin/paster serve development.ini

Should the ``bin/paster`` script not be available in your environment,
install it first using ``bin/pip install PasteScript``.

.. _other SQL databases: http://www.sqlalchemy.org/docs/core/engines.html#supported-databases
.. _variety of web servers: http://wsgi.org/wsgi/Servers
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _Paste Deploy: http://pythonpaste.org/deploy/#the-config-file
