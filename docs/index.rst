.. _index:

=====
Kotti
=====

Kotti is a light-weight, user-friendly and extensible web content
management system.  It is licensed under a `BSD-like license
<http://repoze.org/license.html>`_

Features
========

- **User-friendly**: a simple edit interface hides advanced
  functionality from less experienced users

- **WYSIWYG editor**: includes a rich text editor that lets you edit
  content like in office applications

- **Security**: advanced user, groups and user roles management; uses
  `access control lists`_ (ACL) to control access to different parts
  of the site

- **Templating**: extend Kotti with your own look & feel with very
  little programming required

- **Customizable**: Many aspects of Kotti are configured through a
  simple INI file

- **Add-ons**: a plug-in system allows third party software to greatly
  extend Kotti

- **Pluggable authentication**: allows authentication of users through
  LDAP or other existing user databases

- **Open**: built on top of well-documented, open source components,
  such as Python_, Pyramid_ and SQLAlchemy_

- **Tested**: `continuous testing`_ with a test coverage of 100%
  guarantees Kotti's stability

Try it out
==========

You can try out Kotti on `Kotti's demo site`_.

Under the hood
==============

Kotti is written in Python_ and builds upon on the two excellent
libraries Pyramid_ and SQLAlchemy_.  Kotti tries to leverage these
libraries as much as possible, thus:

- minimizing the amount of code and extra concepts, and

- allowing users familiar with Pyramid and SQLAlchemy to feel right at
  home since Kotti's API is mostly that of Pyramid and SQLAlchemy.

.. _access control lists: http://en.wikipedia.org/wiki/Access_control_list
.. _Kotti's demo site: http://kottidemo.danielnouri.org/
.. _Python: http://www.python.org/
.. _Pyramid: http://docs.pylonsproject.org/projects/pyramid/dev/
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _continuous testing: http://jenkins.danielnouri.org/job/Kotti/

.. _installation:

Installation
============

.. toctree::

   installation.rst

Configuration and customization
===============================

.. toctree::

  configuration.rst

Writing add-ons
===============

.. toctree::

  add-ons.rst

Cookbook
========

.. toctree::

  cookbook/i18n.rst
  cookbook/as-a-library.rst

Contact us
==========

Kotti itself is `developed on Github`_.  The `issue tracker`_ also lives
there.

Have a question or a suggestion?  Write to `Kotti's mailing list`_ or
find us on IRC on irc.freenode.net in channel ``#kotti``.

.. _developed on Github: https://github.com/Pylons/Kotti
.. _issue tracker: https://github.com/Pylons/Kotti/issues
.. _Kotti's mailing list: http://groups.google.com/group/kotti

Tests
=====

To run Kotti's automated test suite, do:

.. code-block:: bash

  bin/py.test

Or alternatively:

.. code-block:: bash

  bin/python setup.py test

You can also run the tests against a different database using the
``KOTTI_TEST_DB_STRING`` environment variable.  By default, Kotti uses
an in-memory SQLite database.  An example:

.. code-block:: bash

  KOTTI_TEST_DB_STRING=postgresql://kotti:kotti@localhost:5432/kotti-testing bin/python setup.py test

**Important**: Never use this feature against a production
database. It will destroy your data.

API
===

.. toctree::

   api
