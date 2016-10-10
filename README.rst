=====
Kotti
=====

|pypi|_
|downloads_month|_
|license|_
|build_status_stable|_

.. |pypi| image:: https://img.shields.io/pypi/v/Kotti.svg?style=flat-square
.. _pypi: https://pypi.python.org/pypi/Kotti/

.. |downloads_month| image:: https://img.shields.io/pypi/dm/Kotti.svg?style=flat-square
.. _downloads_month: https://pypi.python.org/pypi/Kotti/

.. |license| image:: https://img.shields.io/pypi/l/Kotti.svg?style=flat-square
.. _license: http://www.repoze.org/LICENSE.txt

.. |build_status_stable| image:: https://img.shields.io/travis/Kotti/Kotti/stable.svg?style=flat-square
.. _build_status_stable: http://travis-ci.org/Kotti/Kotti

Kotti is a high-level, Pythonic web application framework based on Pyramid_ and SQLAlchemy_.
It includes an extensible Content Management System called the Kotti CMS (see below).

Kotti is most useful when you are developing applications that

- have complex security requirements,
- use workflows, and/or
- work with hierarchical data.

Built on top of a number of *best-of-breed* software components,
most notably Pyramid_ and SQLAlchemy_,
Kotti introduces only a few concepts of its own,
thus hopefully keeping the learning curve flat for the developer.


.. _Pyramid: http://docs.pylonsproject.org/projects/pyramid/dev/
.. _SQLAlchemy: http://www.sqlalchemy.org/

Kotti CMS
=========

You can **try out the Kotti CMS** on `Kotti's demo page`_.

Kotti CMS is a content management system that's heavily inspired by Plone_.
Its **main features** are:

- **User-friendliness**: editors can edit content where it appears;
  thus the edit interface is contextual and intuitive

- **WYSIWYG editor**: includes a rich text editor

- **Responsive design**: Kotti builds on `Bootstrap`_, which
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
.. _Bootstrap: http://getbootstrap.com/

License
=======

Kotti is offered under the BSD-derived `Repoze Public License <http://repoze.org/license.html>`_.

Install
=======

See `installation instructions`_.

.. _installation instructions: https://kotti.readthedocs.io/en/latest/first_steps/installation.html

Support and Documentation
=========================

Read Kotti's extensive `documentation <https://kotti.readthedocs.io/>`_ on `Read the Docs <https://readthedocs.org/>`_.

If you have questions or need help, you can post on our `mailing list / forum <http://groups.google.com/group/kotti>`_ or join us on IRC: `#kotti on irc.freenode.net <irc://irc.freenode.net/#kotti>`_.

If you think you found a bug, open an issue on our `Github bugtracker <https://github.com/Kotti/Kotti/issues>`_.

Development
===========

|build_status_master|_
|coveralls|_
|codacy|_
|codeclimate|_
|quantifiedcode|_
|landscape|_



.. requirements need to be upgraded before we shoff off
   |requires.io|_

|gh_forks|_
|gh_stars|_

Kotti is actively developed and maintained.
We adhere to `high quality coding standards`_, have an extensive test suite with `high coverage`_ and use `continuous integration`_.

Contributions are always welcome, read our `contribution guidelines`_ and visit our `Github repository`_.

.. |build_status_master| image:: https://img.shields.io/travis/Kotti/Kotti/master.svg?style=flat-square
.. _build_status_master: http://travis-ci.org/Kotti/Kotti
.. _continuous integration: http://travis-ci.org/Kotti/Kotti

.. |requires.io| image:: https://img.shields.io/requires/github/Kotti/Kotti.svg?style=flat-square
.. _requires.io: https://requires.io/github/Kotti/Kotti/requirements/?branch=master

.. |gh_forks| image:: https://img.shields.io/github/forks/Kotti/Kotti.svg?style=flat-square
.. _gh_forks: https://github.com/Kotti/Kotti/network

.. |gh_stars| image:: https://img.shields.io/github/stars/Kotti/Kotti.svg?style=flat-square
.. _gh_stars: https://github.com/Kotti/Kotti/stargazers

.. |coveralls| image:: https://img.shields.io/coveralls/Kotti/Kotti.svg?style=flat-square
.. _coveralls: https://coveralls.io/r/Kotti/Kotti
.. _high coverage: https://coveralls.io/r/Kotti/Kotti

.. |codacy| image:: https://img.shields.io/codacy/ad44331fcd904d338c074f2ca3e6a810.svg?style=flat-square
.. _codacy: https://www.codacy.com/public/disko/Kotti
.. _high quality coding standards: https://www.codacy.com/public/disko/Kotti

.. |codeclimate| image:: https://img.shields.io/codeclimate/github/Kotti/Kotti.svg?style=flat-square
.. _codeclimate: https://codeclimate.com/github/Kotti/Kotti

.. |quantifiedcode| image:: http://www.quantifiedcode.com/api/v1/project/f2a648c15f8e42788aaa4fa12a82df93/badge.svg
.. _quantifiedcode: http://www.quantifiedcode.com/app/project/f2a648c15f8e42788aaa4fa12a82df93

.. |landscape| image:: https://landscape.io/github/Kotti/Kotti/master/landscape.svg?style=flat-square
.. _landscape: https://landscape.io/github/Kotti/Kotti

.. _contribution guidelines: https://kotti.readthedocs.io/en/latest/contributing.html
.. _Github repository: https://github.com/Kotti/Kotti
