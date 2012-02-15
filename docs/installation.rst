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

Finally, to run the application under Pyramid 1.3 and better:

.. code-block:: bash

  bin/pserve development.ini

Or alternatively, with older versions of Pyramid:

.. code-block:: bash

  bin/pip install PasteScript
  bin/paster serve development.ini

.. _other SQL databases: http://www.sqlalchemy.org/docs/core/engines.html#supported-databases
.. _variety of web servers: http://wsgi.org/wsgi/Servers
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _Paste Deploy: http://pythonpaste.org/deploy/#the-config-file
