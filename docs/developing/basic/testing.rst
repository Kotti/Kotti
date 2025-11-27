.. _testing:

Automated tests
===============

Kotti uses `pytest`_, `zope.testbrowser`_ and WebTest_ for automated testing.

Before you can run the tests, you must install Kotti's 'testing' extras.
Inside your Kotti checkout directory, do:

.. code-block:: bash

  bin/pip install -e .[testing]

To then run Kotti's test suite, do:

.. code-block:: bash

  bin/py.test

.. _pytest: http://pytest.org
.. _zope.testbrowser: http://pypi.python.org/pypi/zope.testbrowser
.. _WebTest: http://webtest.pythonpaste.org

Using Kotti's test fixtures/funcargs in third party add-ons' tests
------------------------------------------------------------------

To be able to use all of Kotti's fixtures and funcargs in your own package's tests, you only need to "include" them with a line like this in your ``conftest.py`` file::

  pytest_plugins = "kotti"

Available fixtures
``````````````````

.. automodule:: kotti.tests
   :members:
   :noindex:

Continuous Integration
----------------------

Kotti itself is tested against Python versions 3.9, 3.10, 3.11, 3.12, and 3.13 as well as SQLite, MySQL and PostgreSQL (in every possible combination of those) on every commit (and pull request) via `GitHub Actions`_.

If you want your add-on packages to be tested the same way with additional testing against multiple versions of Kotti (including the current master), you can set up GitHub Actions workflows similar to those in the Kotti repository.

.. _GitHub: https://github.com/
.. _GitHub Actions: https://github.com/Kotti/Kotti/actions
.. _PyPI: http://pypi.python.org/pypi
