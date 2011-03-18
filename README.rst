=====
Kotti
=====

What is Kotti?
==============

*Kotti* is a **user-friendly** `web content management system`_
(WCMS).

Features:

- A simple, **user-friendly** edit interface that hides advanced
  functionality from less experienced content managers.

- Separation of public site and editor interface allows for easier
  **templating**

- Easily extensible with **your own look & feel** with no programming
  required

- a **WYSIWYG editor**

- Advanced user and groups management, `Access control lists`_ (ACL)
  for **fine-grained security control**

- Support for **pluggable authentication** modules and single sign-on

- **Easy configuration** through use of INI files.

- Extensible with **your own content types and views**

Try it out
----------

You can try out Kotti on `Kotti's demo site`_.

Unstable
--------

At this point, Kotti is **experimental**.  You're encouraged to try it
out and give us feedback, but don't use it in production yet.  We're
likely to make fundamental changes to both Kotti's API and its
database structure in weeks to come.

Issue tracker and development
=============================

Kotti is `developed on Github`_.  The `issue tracker`_ also lives
there.

Kotti's mailing list for both users and developers is at
http://groups.google.com/group/kotti

You can also find us on IRC: join the ``#kotti`` channel on
irc.freenode.net.

Requirements
============

Kotti requires Python 2.5 or later to run.

Installation using virtualenv
=============================

It's recommended to install Kotti inside a virtualenv_.

Change into the directory of your Kotti download and issue::

  $ python setup.py install

To run Kotti with the included development profile then type::

  $ paster serve development.ini

To run all tests::

  $ python setup.py nosetests


Installation using buildout
===========================

Alternatively, you can use the provided buildout_ configuration like so::

  $ python bootstrap.py
  $ bin/buildout

To run Kotti with the included development profile then type::

  $ bin/paster serve development.ini

To run all tests::

  $ bin/test


Configuring Kotti
=================

Kotti includes two `Paste Deploy`_ configuration files in
``production.ini`` and ``development.ini``.

There are various ``kotti.*`` configuration variables that allow you
to configure and extend various aspects of Kotti, such as the master
templates and CSS files used in Kotti's UI, the user database
implementation, and the list of available content types.

*kotti.site_title*
------------------

Your site's title.

Mail settings: *mail.default_sender*, *mail.host* and friends
-------------------------------------------------------------

Kotti uses `pyramid_mailer`_ for its e-mailing.  See the
`configuration options in the pyramid_mailer docs`_.

*kotti.templates.master_view* and *kotti.templates.master_edit*
---------------------------------------------------------------

The default configuration for these two variables is::

  kotti.templates.master_view = kotti:templates/view/master.pt
  kotti.templates.master_edit = kotti:templates/edit/master.pt

You may override these to provide your own master templates.

*kotti.templates.base_css*, *kotti.templates.view_css*, and *kotti.templates.edit_css*
--------------------------------------------------------------------------------------

These variables define the CSS files used by the default master
templates.  The factory settings here are::

  kotti.templates.base_css = kotti:static/base.css
  kotti.templates.view_css = kotti:static/view.css
  kotti.templates.edit_css = kotti:static/edit.css

*kotti.principals*
------------------

Kotti comes with a default user database implementation in
``kotti.security.principals``.  You can use the ``kotti.principals``
configuration variable to override the implementation used.  The
default looks like this::

  kotti.principals = kotti.security.principals

*kotti.secret*
--------------

``kotti.secret`` (required) and ``kotti.secret2`` (optional) are used
as salts for various hashing functions.  Also, ``kotti.secret`` is the
password of the default admin user.  (The admin password you should
change immediately after you log in.)

An example::

  kotti.secret = qwerty
  kotti.secret2 = asdfgh

With these settings, to log in as admin, you would log in as ``admin``
with the password ``qwerty``.  **Do not use these defaults in
production.**

``kotti.secret`` is used as a salt to the passwords in the default
user database.  Changing it will result in the user database's
passwords becoming invalid.

*kotti.includes* and *kotti.base_includes*
------------------------------------------

``kotti.includes`` allows for convenient extension of Kotti with
additional views, content types and event handlers.  An example::

  kotti.includes = mypackage.views

You should list here modules that contain an ``includeme`` function.
A ``mypackage.views`` module could have this function, which would
register an edit view for a hypothetical event content type::

  def includeme(config):
      config.add_view(
          edit_event,
          context=Event,
          name='edit',
          permission='edit',
          )

``kotti.base_includes`` is a list of modules that Kotti itself defines
for inclusion.  The default::

  kotti.includes =
    kotti.events kotti.views.view kotti.views.edit
    kotti.views.login kotti.views.site_setup

Note that it's also possible to set these options directly from your
Python package by use of the `kotti.configurators`_ configuration
variable.

*kotti.available_types*
-----------------------

Defines the list of content types available.  The default
configuration here is::

  kotti.available_types = kotti.resources.Document

You may replace or add your own types with this variable.  An
example::

  kotti.available_types =
      kotti.resources.Document
      mypackage.resources.Calendar
      mypackage.resources.Event

``kotti.resources.Document`` is itself a class that's suitable as an
example of a Kotti content type implementation::

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

*kotti.configurators*
---------------------

Requiring users of your package to set all the configuration variables
by hand in ``pasteserve.ini`` is not ideal.  That's why Kotti includes
a configuration variable through which extending packages can set all
other configuration options through Python.  Here's an example of a
function that configures Kotti::

  # in mypackage/__init__.py
  def kotti_configure(config):
      config['kotti.base_includes'] += ' mypackage.views'
      config['kotti.principals'] = 'mypackage.security.principals'

And this is how you'd hook it up in the Paste Serve ini file::
  
  kotti.configurators = mypackage.kotti_configure

*kotti.authn_policy_factory* and *kotti.authz_policy_factory*
-------------------------------------------------------------

You can override the authentication and authorization policy that
Kotti uses.  By default, Kotti uses these factories::

  kotti.authn_policy_factory = kotti.authtkt_factory
  kotti.authz_policy_factory = kotti.acl_factory

These settings correspond to
`pyramid.authentication.AuthTktAuthenticationPolicy`_ and
`pyramid.authorization.ACLAuthorizationPolicy`_ being used.

*kotti.session_factory*
-----------------------

The ``kotti.session_factory`` configuration variable allows the
overriding of the default session factory, which is
`pyramid.session.UnencryptedCookieSessionFactoryConfig`_.

Authentication and Authorization
================================

**We're currently working on a user interface for user management.**

**Authentication** in Kotti is pluggable.  See
``kotti.authn_policy_factory``.

ACL
---

Auhorization in Kotti can be configured through
``kotti.authz_policy_factory``.  The default implementation uses
`inherited access control lists`_.  The default install of Kotti has a
root object with this ACL that's defined in
``kotti.security.SITE_ACL``::

  SITE_ACL = [
      ['Allow', 'system.Everyone', ['view']],
      ['Allow', 'role:viewer', ['view']],
      ['Allow', 'role:editor', ['view', 'add', 'edit']],
      ['Allow', 'role:owner', ['view', 'add', 'edit', 'manage']],
      ]

This makes the site viewable by everyone per default.  You can set the
ACL on the site to your liking.  To lock down the site so that only
authenticated users can view, do::

  from kotti.resources import get_root
  root = get_root(request)
  root.__acl__ = root.__acl__[1:] + [('Allow', 'system.Authenticated', ['view'])]

Roles and groups
----------------

The default install of Kotti maps the ``role:admin`` role to the
``admin`` user.  The effect of which is that the ``admin`` user gains
``ALL_PERMISSIONS`` throughout the site.

Principals can be assigned to roles or groups by use of the
``kotti.security.set_groups`` function, which needs to be passed a
context to work with::

  from kotti.security import set_groups
  set_groups(bobsfolder, 'bob', ['role:owner'])

To list roles and groups of a principal, use
``kotti.security.list_groups``.  Although you're more likely to be
using `Pyramid's security API`_ in your code.

Under the hood
==============

Kotti is written in Python_ and builds upon on the two excellent
libraries Pyramid_ and SQLAlchemy_.  Kotti tries to leverage these
libraries as much as possible, thus:

- minimizing the amount of code and extra concepts, and

- allowing users familiar with Pyramid and SQLAlchemy to feel right at
  home since Kotti's API is mostly that of Pyramid and SQLAlchemy.

For storage, you can configure Kotti to use any relational database
for which there is `support in SQLAlchemy`_.  There's no storage
abstraction apart from that.

Have a question?  Join our mailing list at
http://groups.google.com/group/kotti or read `this blog post`_ for
more implementation details.

License
=======

Kotti is available under the BSD- derived `Repoze Public License`_.

Kotti includes the following third party modules:

- `jquery.toastmessage`_ by Daniel Bremer-Tonn, available under the
  Apache License Version 2.0

Thanks
======

Kotti thanks the `University of Coimbra`_ for their involvement and
support.


.. _web content management system: http://en.wikipedia.org/wiki/Web_content_management_system
.. _Access control lists: http://en.wikipedia.org/wiki/Access_control_list
.. _Kotti's demo site: http://kottidemo.danielnouri.org/
.. _developed on Github: https://github.com/dnouri/Kotti
.. _issue tracker: https://github.com/dnouri/Kotti/issues
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _buildout: http://pypi.python.org/pypi/zc.buildout
.. _Paste Deploy: http://pythonpaste.org/deploy/
.. _pyramid_mailer: http://docs.pylonsproject.org/thirdparty/pyramid_mailer/
.. _configuration options in the pyramid_mailer docs: http://docs.pylonsproject.org/thirdparty/pyramid_mailer/dev/#configuration
.. _pyramid.authentication.AuthTktAuthenticationPolicy: http://docs.pylonsproject.org/projects/pyramid/dev/api/authentication.html
.. _pyramid.authorization.ACLAuthorizationPolicy: http://docs.pylonsproject.org/projects/pyramid/dev/api/authorization.html
.. _pyramid.session.UnencryptedCookieSessionFactoryConfig: http://docs.pylonsproject.org/projects/pyramid/dev/api/session.html
.. _inherited access control lists: http://www.pylonsproject.org/projects/pyramid/dev/narr/security.html#acl-inheritance-and-location-awareness
.. _Pyramid's security API: http://docs.pylonsproject.org/projects/pyramid/dev/api/security.html
.. _Python: http://www.python.org/
.. _Pyramid: http://docs.pylonsproject.org/projects/pyramid/dev/
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _support in SQLAlchemy: http://www.sqlalchemy.org/docs/core/engines.html#supported-databases
.. _this blog post: http://danielnouri.org/notes/2010/01/25/16-hours-into-a-new-cms-with-pyramid/
.. _Repoze Public License: http://repoze.org/LICENSE.txt
.. _jquery.toastmessage: http://plugins.jquery.com/project/jquery-toastmessage-plugin
.. _University of Coimbra: http://uc.pt/
