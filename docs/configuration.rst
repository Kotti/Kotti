INI File
--------

Kotti is configured using an INI configuration file.  The
installation_ section explains how to get hold of a sample
configuration file.  The ``[app:main]`` section in it might look like
this:

.. code-block:: ini

  [app:main]
  use = egg:Kotti
  pyramid.reload_templates = true
  pyramid.debug_authorization = false
  pyramid.debug_notfound = false
  pyramid.debug_routematch = false
  pyramid.debug_templates = true
  pyramid.default_locale_name = en
  pyramid.includes = pyramid_debugtoolbar
                     pyramid_tm
  mail.default_sender = yourname@yourhost
  sqlalchemy.url = sqlite:///%(here)s/Kotti.db
  kotti.site_title = Kotti
  kotti.secret = changethis1

Various aspects of your site can be changed right here.

Overview of settings
--------------------

This table provides an overview of available settings.  All these
settings must go into the ``[app:main]`` section of your Paste Deploy
configuration file.

===========================  ===================================================
Setting                      Description                            
===========================  ===================================================
**kotti.site_title**         The title of your site
**kotti.secret**             Secret token used as initial admin password
kotti.secret2                Secret token used for email password reset token

**sqlalchemy.url**           `SQLAlchemy database URL`_
**mail.default_sender**      Sender address for outgoing email
mail.host                    Email host to send from

kotti.includes               List of Python configuration hooks
kotti.available_types        List of active content types
kotti.base_includes          List of base Python configuration hooks
kotti.configurators          List of advanced functions for config
kotti.root_factory           Override Kotti's default Pyramid *root factory*
kotti.populators             List of functions to fill initial database

kotti.templates.api          Override ``api`` used by all templates
kotti.asset_overrides        Override Kotti's templates, CSS files and images.

kotti.authn_policy_factory   Component used for authentication
kotti.authz_policy_factory   Component used for authorization
kotti.session_factory        Component used for sessions

kotti.date_format            Date format to use, default: ``medium``
kotti.datetime_format        Datetime format to use, default: ``medium``
kotti.time_format            Time format to use, default: ``medium``
===========================  ===================================================

Only the settings in bold letters required.  The rest has defaults.

kotti.secret and kotti.secret2
------------------------------

The value of ``kotti.secret`` will define the initial password of the
``admin`` user.  This is the initial user that Kotti creates in the
user database.  So if you put *mysecret* here, use *mysecret* as the
password when you log in as ``admin``.  You may then change the
``admin`` user's password through the web interface.

The ``kotti.secret`` token is also used for signing browser session
cookies.

The ``kotti.secret2`` token is used for signing the password reset
token.

Here's an example.  Make sure you use different values though!

.. code-block:: ini

  kotti.secret = myadminspassword
  kotti.secret2 = $2a$12$VVpW/i1MA2wUUIUHwY6v8O

Adjusting the look & feel with ``kotti.override_assets``
--------------------------------------------------------

In your settings file, set ``kotti.override_assets`` to a list of
*asset specifications*.  This allows you to set up a directory in your
package that will mirror Kotti's own and that allows you to override
Kotti's templates, CSS files and images on a case by case basis.

As an example, image that we wanted to override Kotti's master layout
template.  Inside the Kotti source, the layout template is at
``kotti/templates/view/master.pt``.  To override this, we would add a
directory to our own package called ``kotti-overrides`` and therein
put our own version of the template so that the full path to our own
custom template is
``mypackage/kotti-overrides/templates/view/master.pt``.

We can then register our ``kotti-overrides`` directory by use of the
``kotti.asset_overrides`` setting, like so:

.. code-block:: ini

  kotti.asset_overrides = mypackage:kotti-overrides/

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
``kotti.includes`` setting in the ``[app:main]`` section of our INI
file.  (If a line with ``kotti.includes`` does not exist, add it.)

.. code-block:: ini

  kotti.includes = kotti_twitter.include_profile_widget

kotti_twitter also asks us to configure the Twitter widget itself, so
we add some more lines right where we were:

.. code-block:: ini

  kotti_twitter.profile_widget.user = dnouri
  kotti_twitter.profile_widget.loop = true

The order in which the includes are listed matters.  For example, when
you add two slots on the right hand side, the order in which you list
them here will control the order in which they will appear.

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

  kotti.available_types = kotti.resources.Document kotti.resources.File

An example that removes ``File`` and adds two content types:

.. code-block:: ini

  kotti.available_types =
      kotti.resources.Document
      kotti_calendar.resources.Calendar
      kotti_calendar.resources.Event

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
overriding of the default session factory.  By default, Kotti uses
``pyramid_beaker`` for sessions.

.. _repoze.tm2: http://pypi.python.org/pypi/repoze.tm2
.. _SQLAlchemy database URL: http://www.sqlalchemy.org/docs/core/engines.html#database-urls
.. _Pyramid Configurator API: http://docs.pylonsproject.org/projects/pyramid/dev/api/config.html
.. _kotti_twitter: http://pypi.python.org/pypi/kotti_twitter
.. _pyramid.authentication.AuthTktAuthenticationPolicy: http://docs.pylonsproject.org/projects/pyramid/dev/api/authentication.html
.. _pyramid.authorization.ACLAuthorizationPolicy: http://docs.pylonsproject.org/projects/pyramid/dev/api/authorization.html
.. _pyramid.session.UnencryptedCookieSessionFactoryConfig: http://docs.pylonsproject.org/projects/pyramid/dev/api/session.html
