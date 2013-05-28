.. _developer_manual:

Developer manual
================

Read the :ref:`Configuration` section first to understand which hooks
both integrators and developers can use to customize and extend Kotti.

.. contents::

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

.. include:: ../../kotti/tests/nodes.txt
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
``kotti.principals_factory`` which would otherwise be configured by
hand in the INI file:

.. code-block:: python

  # in mypackage/__init__.py
  def kotti_configure(config):
      config['kotti.base_includes'] += ' mypackage.views'
      config['kotti.principals_factory'] = 'mypackage.security.principals'

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

There are views that you might want to override when you override the
principal factory. That is, if you use different columns in the
database, then you will probably want to make changes to the deform
schema as well.

These views are :class:`kotti.views.users.UsersManage`,
:class:`kotti.views.users.UserManage` and
:class:`kotti.views.users.Preferences`. Notice that you should
override them using the standard way, that is, by overriding
``setup_users``, ``setup_user`` or ``prefs`` views. Then you can
override any sub-view used inside them as well as include any logic
for your usecase when it is called, if needed.

Contributing
------------

The Kotti project can use your help in developing the software, requesting
features, reporting bugs, writing developer and end-user documentation -- the
usual assortment for an open source project. Please devote some of your time to
the project.

Contributing to the Code Base
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To contribute to Kotti itself, and to test and run against the master branch
(the current development code base), first create an account on GitHub if you
don't have one. Fork github.com/Kotti/Kotti to your github account, and follow
the usual steps to get a local clone, with origin as your fork, and with
upstream as the pylons/Kotti repo. Then, you will be able to make branches for
contributing, etc. Please read the docs on GitHub if you are new to
development, but the steps, after you have your own fork, would be something
like this:

.. code-block:: bash

  git clone https://github.com/your_github/Kotti.git

  cd Kotti

  git remote add upstream git://github.com/Kotti/Kotti.git

Now you should be set up to make branches for this and that, doing a pull request
from a branch, and the usual git procedures. You may wish to read the
`GitHub fork-a-repo help`_.

.. _GitHub fork-a-repo help: https://help.github.com/articles/fork-a-repo

To run and develop within your clone, do these steps:

.. code-block:: bash

  virtualenv . --no-site-packages

  bin/python setup.py develop

This will create a new virtualenv "in place" and do the python develop steps to
use the Kotti code in the repo.

Run bin/pip install kotti_someaddon, and add a kotti_someaddon entry to app.ini,
as you would do normally, to use add-ons.

You may wish to learn about the `virtualenvwrapper system`_ if you have several
add-ons you develop or contribute to. For example, you could have a development
area devoted to Kotti work, ~/kotti, and in there you could have clones of
repos for various add-ons. And for each, or in some combination, you would use
virtualenvwrapper to create virtualenvs for working with individual add-ons or
Kotti-based projects.  virtualenvwrapper will set these virtualenvs up, by
default, in a directory within your home directory.  With this setup, you can
do ``workon kotti_this`` and ``workon kotti_that`` to switch between different
virtualenvs.  This is handy for maintaining different sets of dependencies and
customizations, and for staying organized.

.. _virtualenvwrapper system: http://virtualenvwrapper.readthedocs.org

Contributing to Developer Docs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Kotti uses the `Sphinx tool`_, using `reStructuredText`_ to write documents,
store in docs/ in a directory structure with .rst files. Use the normal git
procedures for first making a branch, e.g., ``navigation_docs``, then after
making changes, commit, push to this branch on your fork,  and do a pull
request from there, just as you would for contributing to the code base.

In your Kotti clone you can install the requirements for building and viewing
the documents locally:

.. code-block:: bash

  python setup.py docs

  cd docs/

  make html

.. _Sphinx tool: http://sphinx.readthedocs.org

.. _reStructuredText: http://sphinx-doc.org/rest.html

Then you can check the .html files in the _build/ directory locally, before you
do an actual pull request.

The rendered docs are built and hosted on readthedocs.org.

Contributing to User Docs
^^^^^^^^^^^^^^^^^^^^^^^^^

The `Kotti User Manual`_ also uses Sphinx and reStructuredText, but there is a bit
more to the procedure, because several additional tools are used. `Selenium`_
is used for making screen captures, and thereby helps to actually test Kotti in
the process. `blockdiag`_ is used to make flow charts and diagrams interjected
into the docs.

.. _Kotti User Manual: https://kotti-user-manual.readthedocs.org

.. _Selenium: http://selenium-python.readthedocs.org

.. _blockdiag: http://blockdiag.com

Please follow the readme instructions in the `Kotti User Manual repo`_ to get
set up for contributing to the user manual. Of course, you can do pull requests
that change only the text, but please get set up for working with graphics
also, because this is a way to do the important task of keeping Kotti user docs
up-to-date, guaranteed to have graphics in sync with the latest Kotti version.

.. _Kotti User Manual repo: https://github.com/Kotti/kotti_user_manual

The rendered docs are built and hosted on readthedocs.org.

API
---

.. toctree::

   ../api/index.rst


.. _Pyramid's security API: http://docs.pylonsproject.org/projects/pyramid/dev/api/security.html
.. _inherited access control lists: http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/security.html#acl-inheritance-and-location-awareness
