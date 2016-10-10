.. _overview:

Overview
========

Kotti is most useful when you are developing CMS-like applications that

- have complex security requirements,
- use workflows, and/or
- work with hierarchical data.

Built on top of a number of *best-of-breed* software components, most notably Pyramid_ and SQLAlchemy_, Kotti introduces only a few concepts of its own, thus hopefully keeping the learning curve flat for the developer.

.. _Pyramid: http://docs.pylonsproject.org/projects/pyramid/dev/
.. _SQLAlchemy: http://www.sqlalchemy.org/

Features
--------

You can **try out the default installation** on `Kotti's demo page`_.

The Kotti CMS is a content management system that's heavily inspired by Plone_.
Its **main features** are:

- **User-friendliness**: editors can edit content where it appears;
  thus the edit interface is contextual and intuitive

- **WYSIWYG editor**: includes a rich text editor

- **Responsive design**: Kotti builds on `Twitter Bootstrap`_, which
  looks good both on desktop and mobile

- **Templating**: easily extend the CMS with your own look & feel with
  little programming required (see :ref:`static-resource-management`)

- **Add-ons**: install a variety of add-ons and customize them as well
  as many aspects of the built-in CMS by use of an INI configuration
  file (see :ref:`configuration`)

- **Security**: the advanced user and permissions management is
  intuitive and scales to fit the requirements of large organizations

- **Internationalized**: the user interface is fully translatable,
  Unicode is used everywhere to store data (see :ref:`translations`)

.. _Kotti's demo page: http://kottidemo.danielnouri.org/
.. _Plone: http://plone.org/
.. _Twitter Bootstrap: http://twitter.github.com/bootstrap/

For developers
--------------

For developers, Kotti delivers a strong foundation for building different types of web applications that either extend or replace the built-in CMS.

Developers can add and modify through a well-defined API:

- views,
- templates and layout (both via Pyramid_),
- :ref:`content-types`,
- "portlets" (see :mod:`kotti.views.slots`),
- access control and the user database (see :ref:`develop-security`),
- workflows (via `repoze.workflow`_),
- and much more.

Kotti has a **down-to-earth** API.
Developers working with Kotti will most of the time make direct use of the Pyramid_ and SQLAlchemy_ libraries.
Other notable components used but not enforced by Kotti are Colander_ and Deform_ for forms, and Chameleon_ for templating.

Kotti itself is `developed on Github`_.
You can check out Kotti's source code via its GitHub repository.
Use this command:

.. code-block:: bash

  git clone git@github.com:Kotti/Kotti

`Continuous testing`_ against different versions of Python and with *PostgreSQL*, *MySQL* and *SQLite* and a complete test coverage make Kotti a **stable** platform to work with.  |build_status|_

Support
-------

- Python 2.7 (Python 3 coming soon)
- Support for PostgreSQL, MySQL and SQLite (tested regularly), and a list of `other SQL databases`_
- Support for WSGI and a `variety of web servers`_, including Apache


.. _repoze.workflow: http://docs.repoze.org/workflow/
.. _Chameleon: http://chameleon.repoze.org/
.. _Colander: http://docs.pylonsproject.org/projects/colander/en/latest/
.. _continuous testing: http://travis-ci.org/Kotti/Kotti
.. _Deform: http://docs.pylonsproject.org/projects/deform/en/latest/
.. _developed on Github: https://github.com/Kotti/Kotti
.. |build_status| image:: https://secure.travis-ci.org/Kotti/Kotti.png?branch=master
.. _build_status: http://travis-ci.org/Kotti/Kotti
.. _installation:
.. _other SQL databases: http://www.sqlalchemy.org/docs/core/engines.html#supported-databases
.. _variety of web servers: http://wsgi.org/wsgi/Servers
