.. _configuration:

Configuration
=============

.. contents::

INI File
--------

Kotti is configured using an INI configuration file.
The :ref:`installation` section explains how to get hold of a sample configuration file.
The ``[app:kotti]`` section in it might look like this:

.. code-block:: ini

  [app:kotti]
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

This table provides an overview of available settings.
All these settings must go into the ``[app:kotti]`` section of your Paste Deploy configuration file.

Only the settings in bold letters required.
The rest has defaults.

Do take a look at the required settings (in bold) and adjust them in your site's configuration.
A few of the settings are less important, and sometimes only used by developers, not integrators.

=====================================  =========================================
Setting                                Description
=====================================  =========================================
**kotti.site_title**                   The title of your site
**kotti.secret**                       Secret token used for the initial admin password
kotti.secret2                          Secret token used for email password reset token
**sqlalchemy.url**                     `SQLAlchemy database URL`_
**mail.default_sender**                Sender address for outgoing email
kotti.asset_overrides                  Override Kotti's templates
kotti.authn_policy_factory             Component used for authentication
kotti.authz_policy_factory             Component used for authorization
kotti.available_types                  List of active content types
kotti.base_includes                    List of base Python configuration hooks
kotti.caching_policy_chooser           Component for choosing the cache header policy
kotti.configurators                    List of advanced functions for config
kotti.date_format                      Date format to use, default: ``medium``
kotti.datetime_format                  Datetime format to use, default: ``medium``
kotti.depot_mountpoint                 Configure the mountpoint for the blob storage.  See :ref:`blobs` for details.
kotti.depot_replace_wsgi_file_wrapper  Replace you WSGI server's file wrapper with :class:`pyramid.response.FileIter`.
kotti.depot.*.*                        Configure the blob storage.  See :ref:`blobs` for details.
kotti.fanstatic.edit_needed            List of static resources used for edit interface
kotti.fanstatic.view_needed            List of static resources used for public interface
kotti.login_success_callback           Override Kotti's default ``login_success_callback`` function
kotti.max_file_size                    Max size for file uploads, default: ``10`` (MB)
kotti.modification_date_excludes       List of attributes in dotted name notation that should not trigger an update of ``modification_date`` on change
kotti.populators                       List of functions to fill initial database
kotti.request_factory                  Override Kotti's default request factory
kotti.reset_password_callback          Override Kotti's default ``reset_password_callback`` function
kotti.root_factory                     Override Kotti's default Pyramid *root factory*
kotti.sanitize_on_write                Configure :ref:`sanitizers` to be used on write access to resource objects
kotti.sanitizers                       Configure available :ref:`sanitizers`
kotti.search_content                   Override Kotti's default search function
kotti.session_factory                  Component used for sessions
kotti.templates.api                    Override ``api`` object available in templates
kotti.time_format                      Time format to use, default: ``medium``
kotti.url_normalizer                   Component used for url normalization
kotti.zcml_includes                    List of packages to include the ZCML from
mail.host                              Email host to send from
pyramid.default_locale_name            Set the user interface language, default ``en``
pyramid.includes                       List of Python configuration hooks
=====================================  =========================================

kotti.secret and kotti.secret2
------------------------------

The value of ``kotti.secret`` will define the initial password of the ``admin`` user.
Thus, if you define ``kotti.secret = mysecret``, the admin password will be ``mysecret``.
Log in and change the password at any time through the web interface.

The ``kotti.secret`` token is also used for signing browser session cookies.
The ``kotti.secret2`` token is used for signing the password reset token.

Here's an example:

.. code-block:: ini

  kotti.secret = myadminspassword
  kotti.secret2 = $2a$12$VVpW/i1MA2wUUIUHwY6v8O

.. note:: Do not use these values in your site

.. _asset_overrides:

Override templates (``kotti.asset_overrides``)
----------------------------------------------

In your settings file, set ``kotti.asset_overrides`` to a list of *asset specifications*.
This allows you to set up a directory in your package that will mirror Kotti's own and that allows you to override Kotti's templates on a case by case basis.

As an example, image that we wanted to override Kotti's master layout template.
Inside the Kotti source, the layout template is located at ``kotti/templates/view/master.pt``.
To override this, we would add a directory to our own package called ``kotti-overrides`` and therein put our own version of the template so that the full path to our own custom template is ``mypackage/kotti-overrides/templates/view/master.pt``.

We can then register our ``kotti-overrides`` directory by use of the ``kotti.asset_overrides`` setting, like so:

.. code-block:: ini

  kotti.asset_overrides = mypackage:kotti-overrides/

Use add-ons
-----------

Add-ons will usually include in their installation instructions which settings one should modify to activate them.
Configuration settings that are used to activate add-ons are:

- ``pyramid.includes``
- ``kotti.available_types``
- ``kotti.base_includes``
- ``kotti.configurators``

.. _pyramid.includes:

pyramid.includes
````````````````

``pyramid.includes`` defines a list of hooks that will be called when your Kotti app starts up.
This gives the opportunity to third party packages to add registrations to the *Pyramid Configurator API* in order to configure views and more.

Here's an example.
Let's install the `kotti_twitter`_ extension and add a Twitter profile widget to the right column of all pages.
First we install the package from PyPI:

.. code-block:: bash

  bin/pip install kotti_twitter

Then we activate the add-on in our site by editing the ``pyramid.includes`` setting in the ``[app:kotti]`` section of our INI file (if a line with ``pyramid.includes`` does not exist, add it).

.. code-block:: ini

  pyramid.includes = kotti_twitter.include_profile_widget

kotti_twitter also asks us to configure the Twitter widget itself, so we add some more lines right where we were:

.. code-block:: ini

  kotti_twitter.profile_widget.user = dnouri
  kotti_twitter.profile_widget.loop = true

The order in which the includes are listed matters.
For example, when you add two slots on the right hand side, the order in which you list them in ``pyramid.includes`` will control the order in which they will appear.
As an example, here's a configuration with which the search widget will be displayed above the profile widget:

.. code-block:: ini

  pyramid.includes =
      kotti_twitter.include_search_widget
      kotti_twitter.include_profile_widget

Read more about `including packages using 'pyramid.includes'`_ in the Pyramid documentation.

.. _including packages using 'pyramid.includes': http://readthedocs.org/docs/pyramid/en/1.3-branch/narr/environment.html#including-packages

.. _kotti.available_types:

kotti.available_types
`````````````````````

The ``kotti.available_types`` setting defines the list of content types available.
The default configuration here is:

.. code-block:: ini

  kotti.available_types = kotti.resources.Document kotti.resources.File

An example that removes ``File`` and adds two content types:

.. code-block:: ini

  kotti.available_types =
      kotti.resources.Document
      kotti_calendar.resources.Calendar
      kotti_calendar.resources.Event

.. _kotti.populators:

kotti.populators
````````````````

The default configuration here is:

.. code-block:: ini

  kotti.populators = kotti.populate.populate

Populators are functions with no arguments that get called on system startup.
They may then make automatic changes to the database (before calling ``transaction.commit()``).

.. _kotti.search_content:

kotti.search_content
````````````````````

Kotti provides a simple search over the content types based on kotti.resources.Content.
The default configuration here is:

.. code-block:: ini

  kotti.search_content = kotti.views.util.default_search_content

You can provide an own search function in an add-on and register this in your INI file.
The return value of the search function is a list of dictionaries, each representing a search result:

.. code-block:: python

  [{'title': 'Title of search result 1',
    'description': 'Description of search result 1',
    'path': '/path/to/search-result-1'},
   {'title': 'Title of search result 2',
    'description': 'Description of search result 2',
    'path': '/path/to/search-result-2'},
   ...
   ]

An add-on that defines an alternative search function is `kotti_solr`_, which provides an integration with the `Solr`_ search engine.

.. _user interface language:

Configure the user interface language
-------------------------------------

By default, Kotti will display its user interface in English.
The default configuration is:

.. code-block:: ini

  pyramid.default_locale_name = en

You can configure Kotti to serve a German user interface by saying:

.. code-block:: ini

  pyramid.default_locale_name = de_DE

The list of available languages is `here
<https://github.com/Kotti/Kotti/tree/master/kotti/locale>`_.

Configure authentication and authorization
------------------------------------------

You can override the authentication and authorization policy that Kotti uses.
By default, Kotti uses these factories:

.. code-block:: ini

  kotti.authn_policy_factory = kotti.authtkt_factory
  kotti.authz_policy_factory = kotti.acl_factory

These settings correspond to `pyramid.authentication.AuthTktAuthenticationPolicy`_ and `pyramid.authorization.ACLAuthorizationPolicy`_ being used.

Sessions
--------

The ``kotti.session_factory`` configuration variable allows the overriding of the default session factory.
By default, Kotti uses ``pyramid_beaker`` for sessions.

Caching
-------

You can override Kotti's default set of cache headers by changing the ``kotti.views.cache.caching_policies`` dictionary, which maps policies to headers.
E.g. the ``Cache Resource`` entry there caches all static resources for 32 days.
You can also choose which responses match to which caching policy by overriding Kotti's default cache policy chooser through the use of the ``kotti.caching_policy_chooser`` configuration variable.
The default is:

.. code-block:: ini

  kotti.caching_policy_chooser = kotti.views.cache.default_caching_policy_chooser

URL normalization
-----------------

Kotti normalizes document titles to URLs by replacing language specific characters like umlauts or accented characters with its ascii equivalents.
You can change this default behavour by setting ``kotti.url_normalizer.map_non_ascii_characters`` configuration variable to ``False``.
If you do, Kotti will leave national characters in URLs.

You may also replace default component used for url normalization by setting ``kotti.url_normalizer`` configuation variable.

The default configuration here is:

.. code-block:: ini

  kotti.url_normalzier = kotti.url_normalizer.url_normalizer
  kotti.url_normalizer.map_non_ascii_characters = True

Local navigation
----------------

Kotti provides a build in navigation widget, which is disabled by default.
To enable the navigation widget add the following to the ``pyramid.includes`` setting:

.. code-block:: ini

  pyramid.includes = kotti.views.slots.includeme_local_navigation

The add-on `kotti_navigation`_ provides also a navigation widget with more features.
With this add-on included your configuration looks like:

.. code-block:: ini

  pyramid.includes = kotti_navigation.include_navigation_widget

Check the documentation of `kotti_navigation`_ for more options.


.. _repoze.tm2: http://pypi.python.org/pypi/repoze.tm2
.. _SQLAlchemy database URL: http://www.sqlalchemy.org/docs/core/engines.html#database-urls
.. _Pyramid Configurator API: http://docs.pylonsproject.org/projects/pyramid/dev/api/config.html
.. _kotti_twitter: http://pypi.python.org/pypi/kotti_twitter
.. _kotti_navigation: http://pypi.python.org/pypi/kotti_navigation
.. _kotti_solr: http://pypi.python.org/pypi/kotti_solr
.. _Solr: http://lucene.apache.org/solr/
.. _pyramid.authentication.AuthTktAuthenticationPolicy: http://docs.pylonsproject.org/projects/pyramid/dev/api/authentication.html
.. _pyramid.authorization.ACLAuthorizationPolicy: http://docs.pylonsproject.org/projects/pyramid/dev/api/authorization.html
.. _pyramid.session.UnencryptedCookieSessionFactoryConfig: http://docs.pylonsproject.org/projects/pyramid/dev/api/session.html
