=====
Kotti
=====

What is it?
===========

*Kotti* aims to be a **user-friendly** `web content management system`_.

Features:

- Support for **pluggable authentication** modules and single sign-on

- `Access control lists`_ (ACL) for **fine-grained security**

- **Separation** between public area and editor interface

- Separation of basic and advanced functionality in the editor user
  interface; enables a **pleasant learning curve for editos**

- Easily extensible with **your own look & feel**; no programming required

- Easily extensible with **your own content types and views**

Note
----

At this point, Kotti is **experimental**.  You're encouraged to try it
out and give us feedback, but don't use it in production yet.  We're
likely to make fundamental changes to both Kotti's API and its
database structure in the following weeks.

Installation
============

It's recommended to install Kotti inside a virtualenv_.

Change into the directory of your Kotti download and issue::

  $ python setup.py install

To run Kotti with the included development profile then type::

  $ paster serve development.ini

To run all tests::

  $ python setup.py nosetests

Under the hood
==============

Kotti is written in Python_ and based on the two excellent libraries
Pyramid_ and SQLAlchemy_.  Kotti tries to leverage these libraries as
much as possible, thus:

- minimizing the amount of code written,

- and allowing users familiar with these libraries to feel right at
  home.

Kotti aims to use few abstractions, yet it aims to be somewhat
extensible.

You can extend Kotti with new content types and views
from your own Python packages.  If all that you want is replace
templates and styles, then it's sufficient to hook up your static
files in the configuration.

For storage, Kotti uses any relational database for which there is
`support in SQLAlchemy`_.  There's no storage abstraction apart from
that.

Read `this blog post`_ for more implementation details.

Thanks
======

Kotti is proudly sponsored by the `University of Coimbra`_.

.. _web content management system: http://en.wikipedia.org/wiki/Web_content_management_system
.. _Access control lists: http://en.wikipedia.org/wiki/Access_control_list
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _Python: http://www.python.org/
.. _Pyramid: http://docs.pylonsproject.org/projects/pyramid/dev/
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _support in SQLAlchemy: http://www.sqlalchemy.org/docs/core/engines.html#supported-databases
.. _this blog post: http://danielnouri.org/notes/2010/01/25/16-hours-into-a-new-cms-with-pyramid/
.. _University of Coimbra: http://uc.pt/
