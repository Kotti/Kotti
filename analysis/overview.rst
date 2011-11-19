Overview
^^^^^^^^

.. contents::

Kotti is a Traversal_-based application whose resource tree is in a SQL
database. This is unusual because traversal-based applications normally use
ZODB (the Zope Object Database) to store resources at arbitrary URLs, while URL
Dispatch-based applications (with a few fixed URL patterns) use SQL. So Kotti's
code is interesting both as an implementation of a Content Management System
and as an example of a Traversal application with a SQL resource tree.




.. _Traversal: http://docs.pylonsproject.org/projects/pyramid/dev/narr/traversal.html#traversal-chapter
