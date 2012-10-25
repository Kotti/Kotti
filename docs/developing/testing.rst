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
