.. _static-resource-management:

Static resource management
==========================

In the default settings Kotti uses `Fanstatic`_ to manage its static resources (i.e. CSS, JS, etc.).
This is accomplished by a ``WSGI pipeline``:

.. code-block:: ini

    [app:kotti]
    use = egg:kotti

    [filter:fanstatic]
    use = egg:fanstatic#fanstatic

    [pipeline:main]
    pipeline =
        fanstatic
        kotti

    [server:main]
    use = egg:waitress#main
    host = 127.0.0.1
    port = 5000

Defining resources in third party addons
----------------------------------------

Defining your own resources and have them rendered in the pages
produced by Kotti is also easy.  You just need to define resource
objects (`as described in the corresponding Fanstatic documentation`_)
and add them to either ``edit_needed`` or ``view_needed`` in
kotti.fanstatic:

.. code-block:: python

  from fanstatic import Library
  from fanstatic import Resource
  from kotti.fanstatic import edit_needed
  from kotti.fanstatic import view_needed

  my_library = Library('my_package', 'resources')
  my_resource = Resource(my_library, "my.js")

  def includeme(config):
      # add to edit_needed if the resource is needed in edit views
      edit_needed.add(my_resource)
      # add to view_needed if the resource is needed in edit views
      view_needed.add(my_resource)

Don't forget to add an ``entry_point`` to your package's setup.py:

.. code-block:: python

  entry_points={
      'fanstatic.libraries': [
          'foo = my_package:my_library',
          ],
      },

Fanstatic has many more useful options, such as being able to define
additional minified resources for deployment.  Please consult
`Fanstatic's documentation`_ for a complete list of options.

Overriding Kotti's default definitions
--------------------------------------

You can override the resources to be included in the configuration file.

The defaults are

.. code-block:: ini

    [app:kotti]

    kotti.fanstatic.edit_needed = kotti.fanstatic.edit_needed
    kotti.fanstatic.view_needed = kotti.fanstatic.view_needed

which ist actually a shortcut for

.. code-block:: ini

    [app:kotti]

    kotti.fanstatic.edit_needed =
        kotti.fanstatic.edit_needed_js
        kotti.fanstatic.edit_needed_css

    kotti.fanstatic.view_needed =
        kotti.fanstatic.view_needed_js
        kotti.fanstatic.view_needed_css

You may add as many ``kotti.fanstatic.NeededGroup``,
``fanstatic.Group`` or ``fanstatic.Resource`` (or actually anything
that provides a ``.need()`` method) objects in dotted notation as you
want.

Say you want to completely abandon Kotti's CSS resources (and use your
own for both view and edit views) but use Kotti's JS resources plus an
additional JS resource defined within your app (only in edit
views). Your configuration file might look like this:

.. code-block:: ini

    [app:kotti]

    kotti.fanstatic.edit_needed =
        kotti.fanstatic.edit_needed_js
        myapp.fanstatic.js_resource
        myapp.fanstatic.css_resource

    kotti.fanstatic.view_needed =
        kotti.fanstatic.view_needed_js
        myapp.fanstatic.css_resource


Using Kotti without Fanstatic
-----------------------------

To handle resources yourself, you can easily and completely turn off
fanstatic:

.. code-block:: ini

    [app:main]
    use = egg:kotti

    [server:main]
    use = egg:waitress#main
    host = 127.0.0.1
    port = 5000


.. _Fanstatic: http://www.fanstatic.org/
.. _as described in the corresponding Fanstatic documentation: https://fanstatic.readthedocs.io/en/latest/library.html
.. _Fanstatic's documentation: https://fanstatic.readthedocs.io/
