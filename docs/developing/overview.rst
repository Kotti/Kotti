.. _developer_overview:

Developer Overview
==================

For developers, Kotti delivers a strong foundation for building
different types of web applications that either extend or replace the
built-in CMS.

Developers can add and modify through a well-defined API:

- views,
- templates and layout (both via Pyramid_),
- :ref:`content-types`,
- portlets (see :ref:`slots`),
- access control and the user database (see :ref:`develop-security`),
- workflows (via `repoze.workflow`_),
- and much more.

Kotti has a **down-to-earth** API.  Developers working with Kotti will
most of the time make direct use of the Pyramid_ and SQLAlchemy_
libraries.  Other notable components used but not enforced by Kotti
are Colander_ and Deform_ for forms, and Chameleon_ for templating.

Kotti itself is `developed on Github`_.  You can check out Kotti's
source code via its GitHub repostiory.  Use this command:

.. code-block:: bash

  git clone git@github.com:Pylons/Kotti

`Continuous testing`_ against different versions of Python and with
*PostgreSQL*, *MySQL* and *SQLite* and a complete test coverage make
Kotti a **stable** platform to work with.  |build status|_


.. _repoze.workflow: http://docs.repoze.org/workflow/
.. _Chameleon: http://chameleon.repoze.org/
.. _Colander: http://docs.pylonsproject.org/projects/colander/en/latest/
.. _continuous testing: http://travis-ci.org/Pylons/Kotti
.. _Deform: http://docs.pylonsproject.org/projects/deform/en/latest/
.. _developed on Github: https://github.com/Pylons/Kotti
.. |build status| image:: https://secure.travis-ci.org/Pylons/Kotti.png?branch=master
.. _build status: http://travis-ci.org/Pylons/Kotti
.. _installation:
