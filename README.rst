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

Issue tracker and development
=============================

Kotti is `developed on Github`_.  The `issue tracker`_ also lives
there.

Kotti's mailing list for both users and developers is at
http://groups.google.com/group/kotti

You can also find us on IRC: join the ``#kotti`` channel on
irc.freenode.net.

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

*kotti.authn_policy_factory* and *kotti.authz_policy_factory*
-------------------------------------------------------------

You can override the authentication and authorization policy that
Kotti uses.  By default, Kotti uses these factories::

  kotti.authn_policy_factory = kotti.authtkt_factory
  kotti.authz_policy_factory = kotti.acl_factory

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
    kotti.events kotti.views.view kotti.views.edit kotti.views.login kotti.views.manage

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

Changing the ``kotti.includes`` configuration allows you to register
your own views or event handlers instead of Kotti's defaults.  As an
example, consider a scenario where you want to implement your own
management views.  This could be because you're using a user database
implementation that is very different to Kotti's own.  Your
configuration would look something like this::

  kotti.includes =
    kotti.events kotti.views.view kotti.views.edit kotti.views.login mypackage.manage
  kotti.principals = mypackage.manage.principals

Note that it's also possible to set these options directly from your
Python package by use of the `kotti.configurators`_ configuration
variable.

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

*kotti.configurators*
---------------------

Requiring users of your package to set all the configuration variables
by hand in ``pasteserve.ini`` is not ideal.  That's why Kotti includes
a configuration variable through which extending packages can set all
other configuration options through Python.  Here's an example of a
function that configures Kotti::

  # in mypackage/__init__.py
  def kotti_configure(config):
      config['kotti.includes'] += ' mypackage.views'
      config['kotti.principals'] = 'mypackage.security.principals'
      config['kotti.authn_policy_factory'] = 'mypackage.security.authn_factory'

And this is how you'd hook it up in the ``pasteserve.ini``::
  
  kotti.configurators = mypackage.kotti_configure

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
      ['Allow', 'system.Authenticated', ['view']],
      ['Allow', 'role:viewer', ['view']],
      ['Allow', 'role:editor', ['view', 'add', 'edit']],
      ['Allow', 'role:owner', ['view', 'add', 'edit', 'manage']],
      ]

You can see how viewing the site is locked down to authenticated
users.  You can set the ACL through the ``Node.__acl__`` property to
your liking.  To open your site so that everyone can ``view``, do::

  from kotti.resources import get_root
  root = get_root(request)
  root.__acl__ = root.__acl__ + [('Allow', 'system.Everyone'), ['view']]

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

Thanks
======

Kotti thanks the `University of Coimbra`_ for their involvement and
support.


.. _web content management system: http://en.wikipedia.org/wiki/Web_content_management_system
.. _Access control lists: http://en.wikipedia.org/wiki/Access_control_list
.. _developed on Github: https://github.com/dnouri/Kotti
.. _issue tracker: https://github.com/dnouri/Kotti/issues
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _buildout: http://pypi.python.org/pypi/zc.buildout
.. _Paste Deploy: http://pythonpaste.org/deploy/
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
.. _University of Coimbra: http://uc.pt/
