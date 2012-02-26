Using Kotti as a library
========================

Instead of taking control of your application, and delegating to your
extension, you may use Kotti in applications where you define the
``main`` *entry point* yourself.

You'll anyway still need to call ``kotti.base_configure`` from your
code to set up essential parts of Kotti:

.. code-block:: python

  default_settings = {
      'kotti.authn_policy_factory': 'myapp.authn_policy_factory',
      'kotti.base_includes': (
          'kotti kotti.views kotti.views.login kotti.views.users'),
      'kotti.includes': 'myapp myapp.views',
      'kotti.use_tables': 'orders principals',
      'kotti.populators': 'myapp.resources.populate',
      'kotti.principals_factory': 'myapp.security.Principals',
      'kotti.root_factory': 'myapp.resources.Root',
      'kotti.site_title': 'Myapp',
      }

  def main(global_config, **settings):
      settings2 = default_settings.copy()
      settings2.update(settings)
      config = kotti.base_configure(global_config, **settings2)
      return config.make_wsgi_app()

The above example configures Kotti so that its user database and
security subsystem are set up.  Only a handful of tables
(``kotti.use_tables``) and a handful of Kotti's views
(``kotti.base_includes``) are activated.  Furthermore, our application
is configured to use a custom root factory (root node) and a custom
populator.

In your `PasteDeploy` configuration you'd then wire up your app
directly, maybe like this:

.. code-block:: ini

  [app:main]
  use = egg:myapp
  pyramid.includes = pyramid_tm
  mail.default_sender = yourname@yourhost
  sqlalchemy.url = sqlite:///%(here)s/myapp.db
  kotti.secret = secret
