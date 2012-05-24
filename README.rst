=====
Kotti
=====

Kotti is a high-level, *Pythonic* web application framework.  It
includes a small and extensible CMS application called the **Kotti
CMS**.  |build status|_

Kotti is most useful when you are developing applications that

- have complex security requirements,
- use workflows, and/or
- work with hierarchical data.

Built on top of a number of *best-of-breed* software components, most
notably Pyramid_ and SQLAlchemy_, Kotti introduces only a few concepts
of its own, thus hopefully keeping the learning curve flat for the
developer.

.. |build status| image:: https://secure.travis-ci.org/Pylons/Kotti.png?branch=master
.. _build status: http://travis-ci.org/Pylons/Kotti
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
  with almost no programming required

- **Add-ons**: install a variety of add-ons and customize them as well
  as many aspects of the built-in CMS by use of an INI configuration
  file

- **Security**: the advanced user and permissions management is
  intuitive and scales to fit the requirements of large organizations

- **Internationalized**: the user interface is fully translatable,
  Unicode is used everywhere to store data

.. _Kotti's demo page: http://kottidemo.danielnouri.org/
.. _Plone: http://plone.org/
.. _Twitter Bootstrap: http://twitter.github.com/bootstrap/

Support and Documentation
=========================

`Click here to access Kotti's full documentation
<http://kotti.readthedocs.org/>`_

License
=======

Kotti is offered under the BSD-derived `Repoze Public License
<http://repoze.org/license.html>`_.
