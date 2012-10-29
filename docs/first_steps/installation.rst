.. _installation:

Installation
============

Requirements
------------

- Python 2.6 or 2.7
- virtualenv_
- ``build_essential`` and ``python-dev`` (on Debian or Ubuntu)
-  or ``Xcode`` (on OSX)

Installation using ``virtualenv``
---------------------------------

It's recommended to install Kotti inside a virtualenv:

.. code-block:: bash

  virtualenv mysite
  cd mysite
  bin/pip install -r https://raw.github.com/Pylons/Kotti/0.7.2/requirements.txt

Kotti uses `Paste Deploy`_ for configuration and deployment.  An
example configuration file is included with Kotti's source
distribution.  Download it:

.. code-block:: bash

  wget https://github.com/Pylons/Kotti/raw/master/app.ini

Finally, to run Kotti:

.. code-block:: bash

  bin/pserve app.ini

.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _Paste Deploy: http://pythonpaste.org/deploy/#the-config-file
