.. _tut-1:

Tutorial Part 1: Creating an add-on and managing static resources
=================================================================

In the first part of the tutorial, we'll create an add-on package, install and register the package with our site, and use a simple CSS example to learn how Kotti manages static resources.

Kotti add-ons are proper Python packages.
A number of them are available on PyPI_.
They include `kotti_media`_, for adding a set of video and audio content types to a site, `kotti_gallery`_, for adding a photo album content type, `kotti_blog`_, for blog and blog entry content types, etc.

The add-on we will make, ``kotti_mysite``, will be just like those, in that it will be a proper Python package created with the same command line tools used to make `kotti_media`_, `kotti_blog`_, and the others.
We will set up ``kotti_mysite`` for our Kotti site, in the same way that we might wish later to install, for example, `kotti_media`_.

So, we are working in the ``mysite`` directory, a virtualenv, as described in :ref:`installation`.
You should be able to start Kotti, and load the front page.

We will create the add-on as ``mysite/kotti_mysite``.
``kotti_mysite`` will be a proper Python package, installable into our virtualenv.

.. _mailing list: http://groups.google.com/group/kotti
.. _#kotti: //irc.freenode.net/#kotti
.. _PyPI: http://pypi.python.org/pypi?%3Aaction=search&term=kotti_&submit=search/
.. _kotti_media: http://pypi.python.org/pypi/kotti_media/
.. _kotti_gallery: http://pypi.python.org/pypi/kotti_gallery/
.. _kotti_blog: http://pypi.python.org/pypi/kotti_blog/

Creating the Add-On Package
---------------------------

To create our add-on, we use the standard Pyramid tool ``pcreate``, with
``kotti_addon``, a scaffold that was installed as part of Kotti.

.. code-block:: bash

  bin/pcreate -s kotti kotti_mysite

The script will ask a number of questions.
It is safe to accept the defaults.
When finished, observe that a new directory called ``kotti_mysite`` was added to the current working directory, as ``mysite/kotti_mysite``.

Installing Our New Add-On
-------------------------

To install the add-on (or any add-on, as discussed above) into our Kotti site, we'll need to do two things:

- install the package into our virtualenv
- include the package inside our site's ``app.ini``

.. note::

  Why two steps?
  Installation of our add-on as a Python package is different from activating the add-on in our site.
  Consider that you might have multiple add-ons installed in a virtualenv, but you could elect to activate a subset of them, as you experiment or develop add-ons.

To install the package into the virtualenv, we'll change into the new ``kotti_mysite`` directory, and issue a ``python setup.py develop``.
This will install the package in *development mode*:

.. code-block:: bash

  cd kotti_mysite
  ../bin/python setup.py develop

.. note::

  ``python setup.py install`` is for normal installation of a finished package, but here, for ``kotti_mysite``, we will be developing it for some time, so we use ``python setup.py develop``.
  Using this mode, a special link file is created in the site-packages directory of your virtualenv.
  This link points to the add-on directory, so that any changes you make to the software will be reflected immediately without having to do an install again.

Step two is configuring our Kotti site to include our new ``kotti_mysite`` package.
To do this, open the ``app.ini`` file, which you downloaded during :ref:`installation`.
Find the line that says:

.. code-block:: ini

  kotti.configurators = kotti_tinymce.kotti_configure

And add ``kotti_mysite.kotti_configure`` to it:

.. code-block:: ini

  kotti.configurators =
      kotti_tinymce.kotti_configure
      kotti_mysite.kotti_configure

At this point, you should be able to restart the application, but you won't notice anything different.
Let's make a simple CSS change and use it to see how Kotti manages static resources.

Static Resources
----------------

Kotti uses fanstatic_ for managing its static resources.

Take a look at ``kotti_mysite/kotti_mysite/fanstatic.py`` to see how this is done:

.. code-block:: python

  from fanstatic import Group
  from fanstatic import Library
  from fanstatic import Resource


  library = Library("kotti_mysite", "static")

  css = Resource(
      library,
      "styles.css",
      minified="styles.min.css")
  js = Resource(
      library,
      "scripts.js",
      minified="scripts.min.js")

  css_and_js = Group([css, js])

The ``css`` and ``js`` resources each define files we can use for our css and js code.
We will use ``style.css`` in our example.
Also note the ``css_and_js`` group.
It shows up in the configuration code discussed below.

fanstatic_ has a number of cool features -- you may want to check out their homepage to find out more.

A Simple Example
----------------

Let's make a simple CSS change to see how this all works.
Open ``kotti_mysite/kotti_mysite/static/style.css`` and add the following code.

.. code-block:: css

  h1, h2, h3 {
    text-shadow: 4px 4px 2px #ccc;
  }

Now, restart the application and reload the front page.

.. code-block:: bash

  cd ..
  bin/pserve app.ini

Notice how the title has a shadow now?

.. _fanstatic: http://www.fanstatic.org/

Configuring the Package with ``kotti.configurators``
----------------------------------------------------

Remember when we added ``kotti_mysite.kotti_configure`` to the ``kotti.configurators`` setting in the ``app.ini`` configuration file?
This is how we told Kotti to call additional code on start-up, so that add-ons have a chance to configure themselves.
The function in ``kotti_mysite`` that is called on application start-up lives in ``kotti_mysite/kotti_mysite/__init__.py``.
Let's take a look:

.. code-block:: python

  def kotti_configure(settings):
      ...
      settings['kotti.fanstatic.view_needed'] += ' kotti_mysite.fanstatic.css_and_js'
      ...

Here, ``settings`` is a Python dictionary with all configuration variables in the
``[app:kotti]`` section of our ``app.ini``, plus the defaults.
The values of this dictionary are merely strings.
Notice how we add to the string ``kotti.fanstatic.view_needed``.

.. note::

   Note the initial space in ' kotti_mysite.static.css_and_js'.
   This allows a handy use of += on different lines.
   After concatenation of the string parts, blanks will delimit them.

This ``kotti.fanstatic.view_needed`` setting, in turn, controls which resources are loaded in the public interface (as compared to the edit interface).

As you might have guessed, we could have also completely replaced Kotti's resources for the public interface by overriding the ``kotti.fanstatic.view_needed`` setting instead of adding to it, like this:

.. code-block:: python

  def kotti_configure(settings):
      ...
      settings['kotti.fanstatic.view_needed'] = ' kotti_mysite.fanstatic.css_and_js'
      ...

This is useful if you've built your own custom theme.
Alternatively, you can completely :ref:`override the master template <asset_overrides>` for even more control (e.g. if you don't want to use Bootstrap).

See also :ref:`configuration` for a full list of Kotti's configuration variables, and :ref:`static-resource-management` for a more complete discussion of how Kotti handles static resources through fanstatic.

In the :ref:`next part <tut-2>` of the tutorial, we'll add our first content types, and add forms for them.
