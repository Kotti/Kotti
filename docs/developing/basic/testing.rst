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

Available fixtures
``````````````````

.. automodule:: kotti.tests
   :members:
   :noindex:

Continuous Integration
----------------------

Kotti itself is tested against Python versions 2.6 and 2.7 as well as SQLite,
mySQL and PostgreSQL (in every possible combination of those) on every commit
(and pull request) via the excellent `GitHub`_ / `Travis CI`_ hook.

If you want your add-on packages' to be tested the same way with additional
testing against multiple versions of Kotti (including the current master), you
can add a ``.travis.yml`` file to your repo that looks similar to this:
https://raw.github.com/Kotti/kotti_media/master/.travis.yml.

The packages under http://kottipackages.xo7.de/ include all Kotti versions
released on `PyPI` (synced every night at 00:15 CET) and a package built from
the current master on GitHub (created every 15 minutes).

.. _GitHub: https://github.com/
.. _Travis CI: https://travis-ci.org/
.. _PyPI: http://pypi.python.org/pypi
