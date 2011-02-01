=====
Kotti
=====

.. contents::

What is it?
===========

Kotti is a minimal CMS based written in Python and based on the two
most excellent libraries Pyramid_ and SQLAlchemy_.  Kotti tries to
leverage these libraries as much as possible, thus:

- minimizing the amount of code written,

- and allowing users familiar with these frameworks to feel right at
  home.

Kotti aims to use few abstractions, yet it aims to be somewhat
extensible.

You can extend Kotti with new content types and views
from your own Python packages.  If all that you want is replace
templates and styles, then it's sufficient to hook up your static
files in the configuration, i.e. without writing a single line of
Python.

For storage, Kotti uses any relational database for which there is
`support in SQLAlchemy`_.  There's no storage abstraction apart from
that.

At this moment, Kotti is **unstable software**.  You're on your own if
you want to use it.  We're going to break the API and the SQLAlchemy
model in ways that is likely to break your application when you
upgrade to a newer version of Kotti, and we won't support a migration
path.

CMS Features (at this point mostly goals)
=========================================

- Access control lists for fine-grained security

- Separation of public skin and editor interface

- Support for instance-level views; documents may have different views
  based on context

- Easily extend with your own look & feel; no Python required

- Easily extend with new content types and views

Implementation notes
====================

Take a look at `this blog post`_ for more implementation details.

Installation
============

It's recommended to install Kotti inside a virtualenv_.

Change into the directory of your Kotti download and issue::

  $ python setup.py install

To run Kotti with the included development profile then run::

  $ paster serve development.ini

To run all tests::

  $ python setup.py nosetests

Thanks
======

Kotti is proudly sponsored by the `University of Coimbra`_.

.. _Pyramid: http://docs.pylonsproject.org/projects/pyramid/dev/
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _support in SQLAlchemy: http://www.sqlalchemy.org/docs/core/engines.html#supported-databases
.. _this blog post: http://danielnouri.org/notes/2010/01/25/16-hours-into-a-new-cms-with-pyramid/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _University of Coimbra: http://uc.pt/
