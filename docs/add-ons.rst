Screencast
----------

Here's a screencast that guides you through the process of creating a
simple Kotti add-on for visitor comments:

.. raw:: html

   <iframe width="640" height="480" src="http://www.youtube-nocookie.com/embed/GC3tw6Tli54?rel=0" frameborder="0" allowfullscreen></iframe>

Content types
-------------

Defining your own content types is easy.  The implementation of the
Document content type serves as an example here:

.. code-block:: python

  class Document(Content):
      type_info = Content.type_info.copy(
          name=u'Document',
          add_view=u'add_document',
          addable_to=[u'Document'],
          )

      def __init__(self, body=u"", mime_type='text/html', **kwargs):
          super(Document, self).__init__(**kwargs)
          self.body = body
          self.mime_type = mime_type

  documents = Table('documents', metadata,
      Column('id', Integer, ForeignKey('contents.id'), primary_key=True),
      Column('body', UnicodeText()),
      Column('mime_type', String(30)),
  )

  mapper(Document, documents, inherits=Content, polymorphic_identity='document')

You can configure the list of active content types in Kotti by
modifying the `kotti.available_types`_ setting.

Using kotti.populators to create your own root object
`````````````````````````````````````````````````````

If you were to totally customize Kotti, and not even include the stock Document type,
you would need to follow the template provided by Document, with some attention to
detail for configuration and for instantiating a resource hierarchy, especially the 
root object. For example, let's say that you replace Document with a custom type called 
Project (updating available types configuration as needed). In your design, under the 
Project custom type, you might have a hierarchy of other types, the relationships 
determined by how the type_info.addable_to setup is done, and how the parent property 
is set for each record on instantiation. When you instantiate the root Project object, 
the code in the populate() method of resources.py would be something like:

.. code-block:: python

  root = Project(name="", title="Mother Project", propertyOne="Something", parent=None)

NOTE: So, the details are that the root object must have an empty name (name="") and 
the parent is None.

Configuring custom views, subscribers and more
----------------------------------------------

`kotti.includes`_ allows you to hook ``includeme`` functions that
configure your custom views, subscribers and more.  An ``includeme``
function takes the `Pyramid Configurator API`_ object as its sole
argument.  An example:

.. code-block:: python

  def my_view(request):
      from pyramid.response import Response
      return Response('OK')

  def includeme(config):
      config.add_view(my_view)

By adding the *dotted name string* of your ``includeme`` function to
the `kotti.includes`_ setting, you ask Kotti to call it on application
start-up.  An example:

.. code-block:: ini

  kotti.includes = mypackage.views.includeme

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

Security
--------

Kotti builds mostly on `Pyramid's security API`_ and uses its
`inherited access control lists`_ support.  On top of that, Kotti
defines *roles* and *groups* support: Users may be collected in
groups, and groups may be given roles that define permissions.

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

.. _Pyramid's security API: http://docs.pylonsproject.org/projects/pyramid/dev/api/security.html
.. _inherited access control lists: http://www.pylonsproject.org/projects/pyramid/dev/narr/security.html#acl-inheritance-and-location-awareness
