.. _testing:

Automated tests
===============

Kotti uses `pytest`_, `zope.testbrowser`_ and WebTest_ for automated
testing.

Before you can run the tests, you must install Kotti's 'testing'
extras.  Inside your Kotti checkout directory, do:

.. code-block:: bash

  bin/python setup.py dev

To then run Kotti's test suite, do:

.. code-block:: bash

  bin/py.test

.. _pytest: http://pytest.org
.. _zope.testbrowser: http://pypi.python.org/pypi/zope.testbrowser
.. _WebTest: http://webtest.pythonpaste.org

Using Kotti's test fixtures/funcargs in third party add-ons' tests
------------------------------------------------------------------

To be able to use all of Kotti's fixtures and funcargs in your own package's
tests, you only need to "include" them with a line like this in your
``conftest.py`` file::

  pytest_plugins = "kotti"

