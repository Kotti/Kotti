=====
Kotti
=====

What is Kotti?
==============

*Kotti* is a **user-friendly** `web content management system`_
(WCMS).

Features:

- Support for **pluggable authentication** modules and single sign-on

- `Access control lists`_ (ACL) for **fine-grained security**

- **Separation** between public area and editor interface

- Separation of basic and advanced functionality in the editor user
  interface, enabling a **pleasant learning curve for editors**

- Easily extensible with **your own look & feel** with no programming
  required

- Easily extensible with **your own content types and views**

Note
----

At this point, Kotti is **experimental**.  You're encouraged to try it
out and give us feedback, but don't use it in production yet.  We're
likely to make fundamental changes to both Kotti's API and its
database structure in weeks to come.

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

*kotti.authentication_policy_factory* and *kotti.authorization_policy_factory*
------------------------------------------------------------------------------

You can override the authentication and authorization policy that
Kotti uses.  By default, Kotti uses these factories::

  kotti.authentication_policy_factory = kotti.authtkt_factory
  kotti.authorization_policy_factory = kotti.acl_factory

These settings correspond to
`pyramid.authentication.AuthTktAuthenticationPolicy`_ and
`pyramid.authorization.ACLAuthorizationPolicy`_ being used.

*kotti.secret*
--------------

``kotti.secret`` and ``kotti.secret2`` (optional) are used as salts
for various hashing functions.  Also, ``kotti.secret`` is the password
of the default admin user.  (Which you should change immediately.)

An example::

  kotti.secret = qwerty
  kotti.secret2 = asdfgh

With these settings, to log in as admin, you would log in as ``admin``
with the password ``qwerty``.

``kotti.secret`` is used as a salt to the passwords in the default
user database.  Changing it will result in the user database's
passwords becoming invalid.

*kotti.session_factory*
-----------------------

The ``kotti.session_factory`` configuration variable allows the
overriding of the default session factory, which is
`pyramid.session.UnencryptedCookieSessionFactoryConfig`_.

*kotti.principals*
------------------

Kotti comes with a default user database implementation in
``kotti.security.principals``.  You can use the ``kotti.principals``
configuration variable to override the implementation used.  The
default looks like this::

  kotti.principals = kotti.security.principals

*kotti.templates.master_view* and *kotti.templates.master_edit*
---------------------------------------------------------------

The default configuration for these two variables is::

  kotti.templates.master_view = kotti:templates/view/master.pt
  kotti.templates.master_edit = kotti:templates/edit/master.pt

You may override these to provide your own master templates.

*kotti.templates.base_css*, *kotti.templates.view_css*, and *kotti.templates.edit_css*
--------------------------------------------------------------------------------------

These variables define the CSS files used by the default master
templates.  The defaults are::

  kotti.templates.base_css = kotti:static/base.css
  kotti.templates.view_css = kotti:static/view.css
  kotti.templates.edit_css = kotti:static/edit.css

*kotti.includes*
----------------

The default configuration here is::

  kotti.includes =
    kotti.events kotti.views.view kotti.views.edit kotti.views.login

These point to modules that contain an ``includeme`` function.  An
``includeme`` function that registers an edit view for an ``Event``
resource might look like this::

  def includeme(config):
      config.add_view(
          edit_event,
          context=Event,
          name='edit',
          permission='edit',
          )

Examples of views and their registrations are in Kotti itself.  Take a
look at ``kotti.views.view`` and ``kotti.views.edit``.  XXX Need
example extension package.

*kotti.available_types*
-----------------------

The default configuration here is::

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

Authentication and Authorization
================================

**Authentication** in Kotti is pluggable.

**Auhorization** in Kotti is controlled through the use of `inherited
access control lists`_.  By default, the root object has an ACL that
looks like this::

  ('Allow', 'group:admins', ALL_PERMISSIONS)
  ('Allow', 'system.Authenticated', ('view',))
  ('Allow', 'group:editors', ('add', 'edit'))

Principals are assigned to groups through the ``__groups__`` special
variable on ``Nodes``.  Again, the default root object serves as an
example.  Its ``__groups__`` variable is set to ``{'admin':
['group:admins']}``.  Thus, the ``admin`` principal becomes part of
the ``group:admins`` group throughout the site.

You are advised not to alter the ACL through the ``__acl__`` attribute
directly.  Instead, to give ``bob`` editing rights by using the
``kotti.security.set_groups`` API::

  from kotti.security import set_groups
  set_groups(bobsfolder, 'bob', ['group:editors'])

**Kotti currently lacks a user interface for user management.**

Issue tracker and development
=============================

Kotti is `developed on Github`_.  The `issue tracker`_ also lives
there.  You can also find us on IRC: join the ``#kotti`` channel on
irc.freenode.net.

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

You can extend Kotti with new content types and views from your own
Python packages.  If all that you want is replace templates and
stylesheets, then it's sufficient to hook up plain old files in the
configuration.

For storage, Kotti uses any relational database for which there is
`support in SQLAlchemy`_.  There's no storage abstraction apart from
that.

Read `this blog post`_ for more implementation details.

Thanks
======

Kotti thanks the `University of Coimbra`_ for their involvement and
support.


.. _web content management system: http://en.wikipedia.org/wiki/Web_content_management_system
.. _Access control lists: http://en.wikipedia.org/wiki/Access_control_list
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _buildout: http://pypi.python.org/pypi/zc.buildout
.. _Paste Deploy: http://pythonpaste.org/deploy/
.. _pyramid.authentication.AuthTktAuthenticationPolicy: http://docs.pylonsproject.org/projects/pyramid/dev/api/authentication.html
.. _pyramid.authorization.ACLAuthorizationPolicy: http://docs.pylonsproject.org/projects/pyramid/dev/api/authorization.html
.. _pyramid.session.UnencryptedCookieSessionFactoryConfig: http://docs.pylonsproject.org/projects/pyramid/dev/api/session.html
.. _inherited access control lists: http://www.pylonsproject.org/projects/pyramid/dev/narr/security.html#acl-inheritance-and-location-awareness
.. _developed on Github: https://github.com/dnouri/Kotti
.. _issue tracker: https://github.com/dnouri/Kotti/issues
.. _Python: http://www.python.org/
.. _Pyramid: http://docs.pylonsproject.org/projects/pyramid/dev/
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _support in SQLAlchemy: http://www.sqlalchemy.org/docs/core/engines.html#supported-databases
.. _this blog post: http://danielnouri.org/notes/2010/01/25/16-hours-into-a-new-cms-with-pyramid/
.. _University of Coimbra: http://uc.pt/
