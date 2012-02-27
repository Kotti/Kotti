.. _index:

========================================
Kotti: Web Application Framework and CMS
========================================

Kotti is a high-level, *Pythonic* web application framework.  It
includes a small and extensible CMS application called the **Kotti
CMS**.

Kotti is most useful when you are developing applications that

- have complex security requirements,
- use workflows, and/or
- work with hierarchical data.

Built on top of a number of *best-of-breed* software components, most
notably Pyramid_ and SQLAlchemy_, Kotti introduces only a few concepts
itself, thus hopefully keeping the learning curve flat for the
developer.

.. _Pyramid: http://docs.pylonsproject.org/projects/pyramid/dev/
.. _SQLAlchemy: http://www.sqlalchemy.org/

Kotti CMS
=========

You can **try out the built-in CMS** on `Kotti's demo page`_.

The Kotti CMS is a content management system that's heavily inspired
by Plone_.  Its **main features** are:

- **User-friendliness**: editors can edit content where it appears;
  thus the edit interface is contextual and intuitive

- **WYSIWYG editor**: includes a rich text editor

- **Responsive design**: Kotti builds on `Twitter Bootstrap`_, which
  looks good both on desktop and mobile

- **Templating**: you can extend the CMS with your own look & feel
  with almost no programming required (see :ref:`adjust_look_feel`)

- **Add-ons**: install a variety of add-ons and customize them as well
  as many aspects of the built-in CMS by use of an INI configuration
  file (see :ref:`configuration`)

- **Security**: the advanced user and permissions management is
  intuitive and scales to fit the requirements of large organizations

.. _Kotti's demo page: http://kottidemo.danielnouri.org/
.. _Plone: http://plone.org/
.. _Twitter Bootstrap: http://twitter.github.com/bootstrap/

For Developers
==============

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

`Continuous testing`_ against different versions of Python and with
both *PostgreSQL* and *SQLite* and a complete test coverage make Kotti
a **stable** platform to work with.

.. _repoze.workflow: http://docs.repoze.org/workflow/
.. _Chameleon: http://chameleon.repoze.org/
.. _Colander: http://docs.pylonsproject.org/projects/colander/en/latest/
.. _Deform: http://docs.pylonsproject.org/projects/deform/en/latest/
.. _continuous testing: http://jenkins.danielnouri.org/job/Kotti/

.. _installation:

Installation
============

You can download Kotti from the `Python Package Index`_, it takes only
a few moments to install.

.. toctree::

   installation.rst

.. _Python Package Index: http://pypi.python.org/pypi/Kotti

Configuration
=============

.. toctree::

   configuration.rst

Developer manual
================

.. toctree::

   developer-manual.rst

Cookbook
========

.. toctree::

  cookbook/close-for-anonymous.rst
  cookbook/frontpage-different-template.rst
  cookbook/i18n.rst
  cookbook/as-a-library.rst

Support and Development
=======================

Please report any bugs that you find to the `issue tracker`_.

If you've got questions that aren't answered by this documentation,
contact the `Kotti mailing list`_ or join the `#kotti IRC channel`_.

Kotti itself is `developed on Github`_.  You can check out Kotti's
source code via its GitHub repostiory.  Use this command:

.. code-block:: bash

  git clone git@github.com:Pylons/Kotti

.. _issue tracker: https://github.com/Pylons/Kotti/issues
.. _Kotti mailing list: http://groups.google.com/group/kotti
.. _#kotti IRC channel: irc://irc.freenode.net/#kotti
.. _developed on Github: https://github.com/Pylons/Kotti

Automated tests
===============

To run Kotti's automated test suite, do:

.. code-block:: bash

  bin/py.test

Or, alternatively:

.. code-block:: bash

  bin/python setup.py test

Detailed Change History
=======================

.. toctree::
   :maxdepth: 2

   changes.rst

.. include:: ../THANKS.txt
