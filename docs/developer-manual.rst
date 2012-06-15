Developer manual
================

Read the :ref:`Configuration` section first to understand which hooks
both integrators and developers can use to customize and extend Kotti.

.. contents::

Fork and Repo Setup
-------------------

To contribute to Kotti, and to test and run against Master, fork pylons/Kotti to
your github account, and follow the usual steps to get a local clone, with origin
as your fork, and with upstream as the pylons/Kotti repo. Then, you will be able
to make branches for contributing, etc. Steps would be something like this:

.. code-block:: bash

  git clone https://github.com/your_github/Kotti.git

  cd Kotti

  git remote add upstream git://github.com/Pylons/Kotti.git

Now you should be set up to make branches for this and that, doing a pull request
from a branch, and the usual git procedures. You may wish to read the 
`Github fork-a-repo help`_.

.. _Github fork-a-repo help: https://help.github.com/articles/fork-a-repo

To run and develop within your clone, do these steps:

.. code-block:: bash

  virtualenv . --no-site-packages 

  bin/python setup.py develop

This will create a new virtualenv "in place" and do the python develop steps to
use the Kotti code in the repo.

Run bin/pip install kotti_someaddon, and add a kotti_someaddon entry to app.ini,
as you would do normally, to use add-ons.

Screencast tutorial
-------------------

Here's a screencast that guides you through the process of creating a
simple Kotti add-on for visitor comments:

.. raw:: html

   <iframe width="640" height="480" src="http://www.youtube-nocookie.com/embed/GC3tw6Tli54?rel=0" frameborder="0" allowfullscreen></iframe>

.. _content-types:

Content types
-------------

Defining your own content types is easy.  The implementation of the
Document content type serves as an example here:

.. code-block:: python

  from kotti.resources import Content

  class Document(Content):
      id = Column(Integer(), ForeignKey('contents.id'), primary_key=True)
      body = Column(UnicodeText())
      mime_type = Column(String(30))

      type_info = Content.type_info.copy(
          name=u'Document',
          title=_(u'Document'),
          add_view=u'add_document',
          addable_to=[u'Document'],
          )

      def __init__(self, body=u"", mime_type='text/html', **kwargs):
          super(Document, self).__init__(**kwargs)
          self.body = body
          self.mime_type = mime_type

You can configure the list of active content types in Kotti by
modifying the :ref:`kotti.available_types` setting.

Note that when adding a relationship from your content type to another
Node, you will need to add a ``primaryjoin`` parameter to your
relationship.  An example:

.. code-block:: python

  from sqlalchemy.orm import relationship

  class DocumentWithRelation(Document):
    id = Column(Integer, ForeignKey('documents.id'), primary_key=True)
    related_item_id = Column(Integer, ForeignKey('nodes.id'))
    related_item = relationship(
        'Node', primaryjoin='Node.id==DocumentWithRelation.related_item_id')

Add views, subscribers and more
-------------------------------

:ref:`pyramid.includes` allows you to hook ``includeme`` functions
that you can use to add views, subscribers, and more aspects of Kotti.
An ``includeme`` function takes the *Pyramid Configurator API* object
as its sole argument.

Here's an example that'll override the default view for Files:

.. code-block:: python

  def my_file_view(request):
      return {...}

  def includeme(config):
      config.add_view(
          my_file_view,
          name='view',
          permission='view',
          context=File,
          )

To find out more about views and view registrations, please refer to
the `Pyramid documentation`_.

By adding the *dotted name string* of your ``includeme`` function to
the :ref:`pyramid.includes` setting, you ask Kotti to call it on
application start-up.  An example:

.. code-block:: ini

  pyramid.includes = mypackage.views.includeme

.. _Pyramid documentation: http://docs.pylonsproject.org/projects/pyramid/en/latest/

Working with content objects
----------------------------

.. include:: ../kotti/tests/nodes.txt
  :start-after: # end of setup
  :end-before: # start of teardown

.. _slots:

:mod:`kotti.views.slots`
------------------------

.. automodule:: kotti.views.slots

:mod:`kotti.events`
-------------------

.. automodule:: kotti.events

``kotti.configurators``
-----------------------

Requiring users of your package to set all the configuration settings
by hand in the Paste Deploy INI file is not ideal.  That's why Kotti
includes a configuration variable through which extending packages can
set all other INI settings through Python.  Here's an example of a
function that programmatically modified ``kotti.base_includes`` and
``kotti_principals`` which would otherwise be configured by hand in
the INI file:

.. code-block:: python

  # in mypackage/__init__.py
  def kotti_configure(config):
      config['kotti.base_includes'] += ' mypackage.views'
      config['kotti.principals'] = 'mypackage.security.principals'

And this is how your users would hook it up in their INI file:

.. code-block:: ini
  
  kotti.configurators = mypackage.kotti_configure

.. _develop-security:

Security
--------

Kotti uses `Pyramid's security API`_, most notably its support
`inherited access control lists`_ support.  On top of that, Kotti
defines *roles* and *groups* support: Users may be collected in
groups, and groups may be given roles, which in turn define
permissions.

The site root's ACL defines the default mapping of roles to their
permissions:

.. code-block:: python

  root.__acl__ == [
      ['Allow', 'system.Everyone', ['view']],
      ['Allow', 'role:viewer', ['view']],
      ['Allow', 'role:editor', ['view', 'add', 'edit']],
      ['Allow', 'role:owner', ['view', 'add', 'edit', 'manage']],
      ]

Every Node object has an ``__acl__`` attribute, allowing the
definition of localized row-level security.

The :func:`kotti.security.set_groups` function allows assigning roles
and groups to users in a given context.
:func:`kotti.security.list_groups` allows one to list the groups of a
given user.  You may also set the list of groups globally on principal
objects, which are of type :class:`kotti.security.Principal`.

Kotti delegates adding, deleting and search of user objects to an
interface it calls :class:`kotti.security.AbstractPrincipals`.  You
can configure Kotti to use a different ``Principals`` implementation
by pointing the ``kotti.principals_factory`` configuration setting to
a different factory.  The default setting here is:

.. code-block:: ini

  kotti.principals_factory = kotti.security.principals_factory

API
---

.. toctree::

   api.rst


.. _Pyramid's security API: http://docs.pylonsproject.org/projects/pyramid/dev/api/security.html
.. _inherited access control lists: http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/security.html#acl-inheritance-and-location-awareness
