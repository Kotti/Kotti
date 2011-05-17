=========
Kotti CMS
=========

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

- **Tested**: an automated test coverage of 100% guarantees Kotti's
  stability

Try it out
----------

You can try out Kotti on `Kotti's demo site`_.

Under the hood
--------------

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

Installation
============

Requirements
------------

- Runs on Python versions 2.5, 2.6 and 2.7.
- Support for `many SQL databases`_, including SQLite, MySQL and PostgreSQL
- Support for WSGI and a `variety of web servers`_, including Apache

Installation using ``virtualenv``
---------------------------------

It's recommended to install Kotti inside a virtualenv_:

.. code-block:: bash

  virtualenv mysite --no-site-packages
  cd mysite
  bin/pip install Kotti

Kotti uses `Paste Deploy`_ for configuration and deployment.  An
example configuration file is included with Kotti's source
distribution:

.. code-block:: bash

  wget https://github.com/dnouri/Kotti/raw/master/development.ini

Finally, to run the application:

.. code-block:: bash

  bin/paster serve development.ini

An `example configuration file for Buildout`_ also exists.

.. _many SQL databases: http://www.sqlalchemy.org/docs/core/engines.html#supported-databases
.. _variety of web servers: http://wsgi.org/wsgi/Servers
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _Paste Deploy: http://pythonpaste.org/deploy/#the-config-file
.. _example configuration file for Buildout: https://github.com/dnouri/Kotti/raw/master/buildout.cfg

Configuration and customization
===============================

INI File
--------

Kotti is configured using an INI configuration file.  The
installation_ section explains how to get hold of a sample
configuration file.  The ``[app:Kotti]`` section in it might look like
this:

.. code-block:: ini

  [app:Kotti]
  use = egg:Kotti
  default_locale_name = en
  sqlalchemy.url = sqlite:///%(here)s/Kotti.db
  mail.default_sender = yourname@yourhost
  kotti.site_title = My Site
  kotti.secret = changethis1
  kotti.secret2 = changethis2

Various aspects of your site can be changed right here.

Overview of settings
--------------------

This table provides an overview of available settings.  All these
settings must go into the ``[app:Kotti]`` section of your Paste Deploy
configuration file.

===========================  ===========================================
Setting                      Description                            
===========================  ===========================================
**kotti.site_title**         The title of your site
**kotti.secret**             Secret key used for encryption
**kotti.secret2**            Another secret key for encryption

**sqlalchemy.url**           `SQLAlchemy database URL`_
**mail.default_sender**      Sender address for outgoing email
mail.host                    Email host to send from

kotti.includes               List of Python configuration hooks
kotti.available_types        List of active content types
kotti.base_includes          List of base Python configuration hooks
kotti.configurators          List of advanced functions for config
kotti.populators             List of functions to fill initial database

kotti.templates.master_view  Master template used for public views
kotti.templates.master_edit  Master template used for edit screens
kotti.templates.snippets     Override <head> and other common elements
kotti.templates.view_css     CSS file used for public views
kotti.templates.edit_css     CSS file used for edit screens
kotti.templates.base_css     Base CSS file; used for both

kotti.authn_policy_factory   Component used for authentication
kotti.authz_policy_factory   Component used for authorization
kotti.session_factory        Component used for sessions

kotti.date_format            Date format to use, default: ``medium``
kotti.datetime_format        Datetime format to use, default: ``medium``
kotti.time_format            Time format to use, default: ``medium``
===========================  ===========================================

Only the settings in bold letters required.  The rest has defaults.

Adjusting the look & feel
-------------------------

The ``kotti.templates.*`` configuration settings allow you to define
alternative template and CSS files to be used.  An example that
overrides botht the master template for all public views and
configures an alternative CSS file for the edit interface:

.. code-block:: ini

  kotti.templates.master_view = mypackage:templates/master.pt
  kotti.templates.edit_css = mypackage:static/edit.css

Using add-ons
-------------

Add-ons will usually include in their installation instructions which
settings one should modify to activate them.  Configuration settings
that are used to activate add-ons are:

- ``kotti.includes``
- ``kotti.available_types``
- ``kotti.base_includes``
- ``kotti.configurators``

kotti.includes
``````````````

``kotti.includes`` defines a list of hooks that will be called by
Kotti when it starts up.  This gives the opportunity to third party
packages to add registrations to the `Pyramid Configurator API`_ in
order to configure views and more.

As an example, we'll add the `kotti_twitter`_ extension to add a
Twitter profile widget to the right column of all pages.  First we
install the package from PyPI:

.. code-block:: bash

  bin/pip install kotti_twitter

Then we activate the add-on in our site by editing the
``kotti.includes`` setting in the ``[app:Kotti]`` section of our INI
file.  (If a line with ``kotti.includes`` does not exist, add it.)

.. code-block:: ini

  kotti.includes = kotti_twitter.include_profile_widget

kotti_twitter also asks us to configure the Twitter widget itself, so
we add some more lines right where we were:

.. code-block:: ini

  kotti_twitter.profile_widget.user = dnouri
  kotti_twitter.profile_widget.loop = true

The order in which the includes are listed matters.  When you add two
slots on the right hand side, the order in which you list them here
will control the order in which they will appear.

With this configuration, the search widget is displayed on top of the
profile widget:

.. code-block:: ini

  kotti.includes =
      kotti_twitter.include_search_widget
      kotti_twitter.include_profile_widget

kotti.available_types
`````````````````````

The ``kotti.available_types`` setting defines the list of content
types available.  The default configuration here is:

.. code-block:: ini

  kotti.available_types = kotti.resources.Document

An example that adds two content types:

.. code-block:: ini

  kotti.available_types =
      kotti.resources.Document
      mypackage.resources.Calendar
      mypackage.resources.Event

Configuring authentication and authorization
--------------------------------------------

You can override the authentication and authorization policy that
Kotti uses.  By default, Kotti uses these factories:

.. code-block:: ini

  kotti.authn_policy_factory = kotti.authtkt_factory
  kotti.authz_policy_factory = kotti.acl_factory

These settings correspond to
`pyramid.authentication.AuthTktAuthenticationPolicy`_ and
`pyramid.authorization.ACLAuthorizationPolicy`_ being used.

Sessions
--------

The ``kotti.session_factory`` configuration variable allows the
overriding of the default session factory, which is
`pyramid.session.UnencryptedCookieSessionFactoryConfig`_.

.. _SQLAlchemy database URL: http://www.sqlalchemy.org/docs/core/engines.html#database-urls
.. _Pyramid Configurator API: http://docs.pylonsproject.org/projects/pyramid/dev/api/config.html
.. _kotti_twitter: http://pypi.python.org/pypi/kotti_twitter
.. _pyramid.authentication.AuthTktAuthenticationPolicy: http://docs.pylonsproject.org/projects/pyramid/dev/api/authentication.html
.. _pyramid.authorization.ACLAuthorizationPolicy: http://docs.pylonsproject.org/projects/pyramid/dev/api/authorization.html
.. _pyramid.session.UnencryptedCookieSessionFactoryConfig: http://docs.pylonsproject.org/projects/pyramid/dev/api/session.html

Writing add-ons
===============

Content types
-------------

Defining your own content types is easy.  The implementation of the
Document content type serves as an example here:

.. code-block:: python

  class Document(Node):
      type_info = Node.type_info.copy(
          name=u'Document',
          add_view=u'add_document',
          addable_to=[u'Document'],
          )

      def __init__(self, body=u"", mime_type='text/html', **kwargs):
          super(Document, self).__init__(**kwargs)
          self.body = body
          self.mime_type = mime_type

  documents = Table('documents', metadata,
      Column('id', Integer, ForeignKey('nodes.id'), primary_key=True),
      Column('body', UnicodeText()),
      Column('mime_type', String(30)),
  )

  mapper(Document, documents, inherits=Node, polymorphic_identity='document')

You can configure the list of active content types in Kotti by
modifying the `kotti.available_types`_ setting.

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

Contact us
==========

Kotti itself is `developed on Github`_.  The `issue tracker`_ also lives
there.

Have a question or a suggestion?  Write to `Kotti's mailing list`_ or
find us on IRC on irc.freenode.net in channel ``#kotti``.

.. _developed on Github: https://github.com/dnouri/Kotti
.. _issue tracker: https://github.com/dnouri/Kotti/issues
.. _Kotti's mailing list: http://groups.google.com/group/kotti

Tests
=====

To run Kotti's automated test suite, do:

.. code-block:: bash

  bin/python setup.py nosetests

API
===

.. toctree::

   api

