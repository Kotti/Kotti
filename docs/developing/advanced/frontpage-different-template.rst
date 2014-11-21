.. _frontpage-diferent-template:

Use a different template for the front page (or any other page)
===============================================================

This recipe describes a way to override the template used for a
specific object in your database.  Imagine you want your front page to
stand out from the rest of your site and use a unique layout.

We can set the *default view* for any content object by settings its
``default_view`` attribute, which is usually ``None``.  Inside our own
populator (see :ref:`kotti.populators`), we write this:

.. code-block:: python

  from kotti.resources import get_root

  def populate():
      site = get_root()
      site.default_view = 'front-page'

What's left is to register the ``front-page`` view:

.. code-block:: python

  def includeme(config):
      config.add_view(
          name='front-page',
          renderer='myapp:templates/front-page.pt',
      )

.. note::

  If you want to override instead the template of *all pages*, not
  only that of a particluar page, you should look at the
  ``kotti.override_assets`` setting (:ref:`asset_overrides`).
