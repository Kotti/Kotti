Kotti Database Structure
^^^^^^^^^^^^^^^^^^^^^^^^

.. contents::

Introduction
============

Kotti's SQL resource model is defined in the ``kotti.resources`` module. It
contains the following page-related ORM classes:

* Node (nodes)
* Content (contents)
* Document (documents)

and other ORM classes:

* LocalGroup (local_groups)
* Principal (principals)
* Setting (settings)

A web page in Kotti is a ``Document`` instance. ``Document`` is a polymorphic
child of ``Content``, which is a polymorphic child of ``Node``. What is
polymorphism, and how are the tables related? This is best explained from the
bottom up, so we'll start with the most basic class, ``Node``.

Node
====

A resource tree in Pyramid is a nested dict-like structure that is published as a
URL tree. For instance, URL "/help/faq" maps to ``root["help"]["faq"]``. This
is the essence of Traversal routing. A ``Node`` is an item in this nested dict;
i.e., something that can be accessed by URL. (Pyramid also allows URLs without
a corresponding node, and resource trees that start at a sub-URL, but we'll
ignore those in this chapter.) The ``nodes`` table looks like this::

    nodes = Table('nodes', metadata,
        Column('id', Integer, primary_key=True),
        Column('type', String(30), nullable=False),
        Column('parent_id', ForeignKey('nodes.id')),
        Column('position', Integer),
        Column('_acl', JsonType()),

        Column('name', Unicode(50), nullable=False),
        Column('title', Unicode(100)),
        Column('annotations', MutationDict.as_mutable(JsonType)),

        UniqueConstraint('parent_id', 'name'),
    )

The records for the Home page and About page in the default Kotti site look
like this:

.. code-block:: sqlite3

    sqlite> .mode line
    sqlite> .nullvalue NULL
    sqlite> select * from nodes;
             id = 1
           type = document
      parent_id = NULL
       position = NULL
           _acl = [["Allow", "system.Everyone", ["view"]], ["Allow", "role:viewer", ["view"]], ["Allow", "role:editor", ["view", "add", "edit"]], ["Allow", "role:owner", ["view", "add", "edit", "manage"]]]
           name = 
          title = Welcome to Kotti!
    annotations = {}

             id = 2
           type = document
      parent_id = 1
       position = NULL
           _acl = [["Allow", "system.Everyone", ["view"]], ["Allow", "role:viewer", ["view"]], ["Allow", "role:editor", ["view", "add", "edit"]], ["Allow", "role:owner", ["view", "add", "edit", "manage"]]]
           name = about
          title = About Foo World
    annotations = {}


The ORM classes are not interesting from a data perspective, so we won't detail
them here. All ORM classes have a constructor with positional args for their
various column values, and a ``.copy()`` method to clone the instance. The
``Node`` class also has methods to allow it to function in a resource tree.

The mapper *is* interesting, however.

::

    nodes = Table('nodes', metadata,
        Column('id', Integer, primary_key=True),
        Column('type', String(30), nullable=False),
        Column('parent_id', ForeignKey('nodes.id')),
        Column('position', Integer),
        Column('_acl', JsonType()),

        Column('name', Unicode(50), nullable=False),
        Column('title', Unicode(100)),
        Column('annotations', MutationDict.as_mutable(JsonType)),

        UniqueConstraint('parent_id', 'name'),
    )





Content
=======


Document
========

Document (table "documents")

    This stores the page body itself and its MIME type. 
